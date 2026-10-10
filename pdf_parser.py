
#%%

from pathlib import Path
import pandas as pd
import numpy as np
import pymupdf
import re
from collections import Counter, defaultdict
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.pipeline_options import PdfPipelineOptions
from helper_funs import get_neighboring_pages, get_strange_page_numbers, llm_page_number_verification


accelerator_options = AcceleratorOptions(
    device=AcceleratorDevice.CPU
)

pipeline_options = PdfPipelineOptions(
    accelerator_options=accelerator_options
)

docling_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)

def get_docling_regions(file_path, pymupdf_doc):
    result = docling_converter.convert(str(file_path))
    docling_doc = result.document
    docling_regions_by_page = defaultdict(list)
    for reading_order, (item, level) in enumerate(docling_doc.iterate_items()):
        if not hasattr(item, "text"):
            continue
        if not item.prov:
            continue
        # IMPORTANT: use every provenance box, not just item.prov[0]
        for prov_index, prov in enumerate(item.prov):
            page_index = prov.page_no - 1
            bbox = prov.bbox
            page_height = pymupdf_doc[page_index].rect.height
            # Convert Docling bottom-left coordinates
            # to PyMuPDF top-left coordinates
            x0 = bbox.l
            y0 = page_height - bbox.t
            x1 = bbox.r
            y1 = page_height - bbox.b
            docling_regions_by_page[page_index].append({
                "reading_order": reading_order,
                "prov_index": prov_index,
                "label": getattr(item.label, "value", str(item.label)),
                "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                "docling_text": item.text
            })
    return docling_regions_by_page

def rectangle_overlap(block, region):
    """Area of the intersection between a text unit and a Docling region."""

    bx0, by0, bx1, by1 = block[:4]
    rx0 = region["x0"]
    ry0 = region["y0"]
    rx1 = region["x1"]
    ry1 = region["y1"]
    intersection_width = max(0, min(bx1, rx1) - max(bx0, rx0))
    intersection_height = max(0, min(by1, ry1) - max(by0, ry0))
    return intersection_width * intersection_height


def _median(values, default=0.0):
    values = sorted(values)
    if not values:
        return default
    middle = len(values) // 2
    if len(values) % 2:
        return values[middle]
    return (values[middle - 1] + values[middle]) / 2


def get_pymupdf_lines(page, textpage=None):
    """
    Return the atomic text units of a page in the block-like tuple format:

    (x0, y0, x1, y1, text, unit_number, block_type, line_key)

    One tuple per span (plus one per image block).  ``line_key`` identifies the
    physical line the span was taken from, so that ``reorder_blocks_using_docling``
    can rebuild lines and, where necessary, split them again at column gutters.
    """

    if textpage is None:
        page_dict = page.get_text("dict", sort=False)
    else:
        page_dict = page.get_text(
            "dict",
            textpage=textpage,
            sort=False
        )

    span_units = []
    unit_number = 0

    for block_index, block in enumerate(page_dict["blocks"]):

        if block["type"] == 0:

            for line_index, line in enumerate(block["lines"]):

                for span in line["spans"]:

                    span_text = span["text"]

                    if not span_text.strip():
                        continue

                    x0, y0, x1, y1 = span["bbox"]

                    span_units.append((
                        x0,
                        y0,
                        x1,
                        y1,
                        span_text,
                        unit_number,
                        0,
                        ("text", block_index, line_index)
                    ))

                    unit_number += 1

        elif block["type"] == 1:

            x0, y0, x1, y1 = block["bbox"]

            span_units.append((
                x0,
                y0,
                x1,
                y1,
                "",
                unit_number,
                1,
                ("image", block_index, 0)
            ))

            unit_number += 1

    return span_units


# ---------------------------------------------------------------------------
# Reading order
#
# Docling's *boxes* are a good segmentation of the page, but its *reading
# order* is not dependable (on scanned two column pages it regularly emits the
# right hand column before the left, and it sometimes merges both columns into
# a single region).  So the order below is derived geometrically, with a
# recursive whitespace cut, and Docling is used for what it is reliable at:
# grouping lines into paragraphs.
# ---------------------------------------------------------------------------


def _make_line(atoms, reference_height=None):
    """
    Collapse a run of spans into a single line unit.

    Blank spans were dropped upstream, so a space is re-inserted wherever the
    spans are visibly separated (PyMuPDF's OCR output in particular emits one
    span per word with no trailing space).
    """

    atoms = sorted(atoms, key=lambda a: a["x0"])

    if reference_height is None:
        heights = [a["y1"] - a["y0"] for a in atoms if a["y1"] > a["y0"]]
        reference_height = _median(heights, 10.0)

    minimum_space = max(0.2 * reference_height, 0.5)

    pieces = [atoms[0]["text"]]
    for previous, atom in zip(atoms, atoms[1:]):
        separated = atom["x0"] - previous["x1"] > minimum_space
        already_spaced = (
            pieces[-1].endswith((" ", "\t"))
            or atom["text"].startswith((" ", "\t"))
        )
        if separated and not already_spaced:
            pieces.append(" ")
        pieces.append(atom["text"])

    return {
        "x0": min(a["x0"] for a in atoms),
        "y0": min(a["y0"] for a in atoms),
        "x1": max(a["x1"] for a in atoms),
        "y1": max(a["y1"] for a in atoms),
        "text": "".join(pieces),
        "unit_number": min(a["unit_number"] for a in atoms),
        "block_type": atoms[0]["block_type"],
        "atoms": atoms
    }


def _line_height(atoms):
    """Median height of the physical lines the spans came from."""

    extents = defaultdict(lambda: [float("inf"), float("-inf")])
    for atom in atoms:
        if atom["block_type"] != 0:
            continue
        extent = extents[atom["line_key"]]
        extent[0] = min(extent[0], atom["y0"])
        extent[1] = max(extent[1], atom["y1"])

    heights = [high - low for low, high in extents.values() if high > low]
    return _median(heights, default=10.0)


def _build_lines(atoms, reference_height):
    """
    Rebuild physical lines from spans.

    A line is only broken at a gap markedly wider than a line height, which
    keeps tabular material apart without cutting into justified prose.  The
    finer, self-calibrating split happens later, once a real column gutter has
    been measured (see ``_split_unit_at_gutter``).
    """

    minimum_split_gap = max(1.2 * reference_height, 3.0)

    lines_by_key = defaultdict(list)
    for atom in atoms:
        lines_by_key[atom["line_key"]].append(atom)

    lines = []

    for key in sorted(lines_by_key):

        group = sorted(lines_by_key[key], key=lambda a: (a["x0"], a["y0"]))
        current = [group[0]]

        for atom in group[1:]:

            gap = atom["x0"] - max(a["x1"] for a in current)
            centre = (atom["y0"] + atom["y1"]) / 2
            run_centre = _median([(a["y0"] + a["y1"]) / 2 for a in current])
            vertical_jump = abs(centre - run_centre) > 0.6 * reference_height

            if gap >= minimum_split_gap or vertical_jump:
                lines.append(_make_line(current, reference_height))
                current = [atom]
            else:
                current.append(atom)

        lines.append(_make_line(current, reference_height))

    return lines


def _find_gutter(units, reference_height):
    """
    Look for a vertical whitespace corridor that splits ``units`` into two
    side by side groups (i.e. a column gutter).

    Returns ``(corridor_x0, corridor_x1, split_x)`` or ``None``.

    The corridor is looked for in the *narrow* units only.  Units that run the
    full width of the region are either genuine page spanning elements or -
    very often, with OCR - two column lines that were read as one, and either
    way they would hide every gutter on the page if they were allowed into the
    projection.  Whether the corridor is real is then decided from all of the
    units: both sides have to carry a substantial share of the page.
    """

    if len(units) < 4:
        return None

    node_x0 = min(u["x0"] for u in units)
    node_x1 = max(u["x1"] for u in units)
    node_width = node_x1 - node_x0

    minimum_gutter = max(0.8 * reference_height, 5.0)

    if node_width <= 3 * minimum_gutter:
        return None

    narrow = [u for u in units if (u["x1"] - u["x0"]) <= 0.6 * node_width]

    if len(narrow) < 4:
        return None

    allowed_coverage = max(1, int(0.1 * len(narrow)))
    minimum_side = max(2, int(0.15 * len(units)))

    events = []
    for unit in narrow:
        events.append((unit["x0"], 1))
        events.append((unit["x1"], -1))
    events.sort()

    # Maximal runs of x where few narrow units are present.  Runs are merged
    # across the odd intruding unit, so that a single word poking into the
    # gutter does not break the corridor into two useless slivers.
    runs = []
    coverage = 0
    previous_x = None

    for x, delta in events:
        if previous_x is not None and x > previous_x and coverage <= allowed_coverage:
            if runs and abs(runs[-1][1] - previous_x) < 1e-9:
                runs[-1][1] = x
            else:
                runs.append([previous_x, x])
        coverage += delta
        previous_x = x

    best = None

    for low, high in runs:

        if high - low < minimum_gutter or low <= node_x0 or high >= node_x1:
            continue

        # Sides are decided by the middle of the corridor, so a line that
        # merely ends inside it still counts as belonging to its own column.
        split_x = (low + high) / 2

        left = [u for u in units if u["x1"] <= split_x]
        right = [u for u in units if u["x0"] >= split_x]
        crossing = [u for u in units if u["x0"] < split_x < u["x1"]]

        if len(left) < minimum_side or len(right) < minimum_side:
            continue

        left_width = max(u["x1"] for u in left) - min(u["x0"] for u in left)
        right_width = max(u["x1"] for u in right) - min(u["x0"] for u in right)

        # Real columns carry a meaningful share of the width; a hanging indent
        # or a column of list markers does not.
        if left_width < 0.15 * node_width or right_width < 0.15 * node_width:
            continue

        # Prefer the corridor that separates the page most cleanly.  Width
        # alone is not enough: the whitespace beside a column of hanging
        # markers is often wider than the gutter those markers belong to, and
        # choosing it would strand every marker in the gap.
        score = (
            -len(crossing),
            high - low,
            -abs(split_x - ((node_x0 + node_x1) / 2))
        )
        if best is None or score > best[0]:
            best = (score, (low, high, split_x))

    return best[1] if best else None


def _split_unit_at_gutter(unit, low, high, split_x, left_neighbours=(), right_neighbours=()):
    """
    Split a unit that straddles a column gutter.

    Two kinds of unit straddle a gutter.  One is a genuinely page spanning
    element - a running title, a full width heading, a rule - which must not be
    cut.  The other is a body line that was wrongly joined across the gutter,
    which happens constantly with OCR: the corridor is often read as a stray
    character, so there is no clean gap to cut at.

    They are told apart by whether a word actually sits across the dividing
    line, and by position: a body line has column material above and below it
    in both columns, a running title does not.

    Returns the pieces, or ``None`` when the unit should be left whole.
    """

    atoms = unit["atoms"]
    if len(atoms) < 2:
        return None

    # A word lying across the dividing line means the unit spans the page on
    # purpose; cutting it would tear a real word in half.
    if any(a["x0"] < split_x < a["x1"] and any(char.isalnum() for char in a["text"]) for a in atoms):
        return None

    before = [a for a in atoms if a["x1"] <= split_x]
    after = [a for a in atoms if a["x1"] > split_x]

    if not before or not after:
        return [unit]

    # A gutter-sized hole in the line is unambiguous: its two halves belong to
    # different columns.  The hole is measured between the words and ignores
    # any non-alphanumeric atom lying over the corridor, because OCR regularly
    # reads the gutter itself as a stray mark - and that mark would otherwise
    # fill the very gap being measured.  Only the measurement ignores it; the
    # mark is still carried into whichever piece it falls in.
    carrying_text = [
        a for a in atoms
        if any(char.isalnum() for char in a["text"])
        or not (a["x0"] < high and a["x1"] > low)
    ]
    words_before = [a for a in carrying_text if a["x1"] <= split_x]
    words_after = [a for a in carrying_text if a["x1"] > split_x]

    if words_before and words_after:
        hole = (
            min(a["x0"] for a in words_after)
            - max(a["x1"] for a in words_before)
        )
        if hole >= 0.5 * (high - low):
            return [_make_line(before), _make_line(after)]

    if not left_neighbours or not right_neighbours:
        return None

    centre_y = (unit["y0"] + unit["y1"]) / 2

    sandwiched = all(
        any(n["y1"] <= centre_y for n in side)
        and any(n["y0"] >= centre_y for n in side)
        for side in (left_neighbours, right_neighbours)
    )

    if not sandwiched:
        return None

    return [_make_line(before), _make_line(after)]


def _split_on_axis(units, axis, minimum_gap):
    """Group units into runs separated by gaps of at least ``minimum_gap``."""

    low_key = "x0" if axis == "x" else "y0"
    high_key = "x1" if axis == "x" else "y1"

    ordered = sorted(units, key=lambda u: (u[low_key], u[high_key]))

    groups = [[ordered[0]]]
    running_high = ordered[0][high_key]

    for unit in ordered[1:]:
        if unit[low_key] - running_high >= minimum_gap:
            groups.append([unit])
            running_high = unit[high_key]
        else:
            groups[-1].append(unit)
            running_high = max(running_high, unit[high_key])

    return groups


def _sort_by_line(units, reference_height):
    """Plain left to right, top to bottom order with a baseline tolerance."""

    tolerance = max(0.5 * reference_height, 1.0)
    ordered = sorted(units, key=lambda u: (u["y0"], u["x0"]))

    rows = []
    for unit in ordered:
        if rows and unit["y0"] - rows[-1][0] <= tolerance:
            rows[-1][1].append(unit)
        else:
            rows.append((unit["y0"], [unit]))

    result = []
    for _row_top, row in rows:
        result.extend(sorted(row, key=lambda u: u["x0"]))
    return result


def _order_region(units, reference_height, depth=0):
    """Recursive whitespace cut: columns first, then horizontal bands."""

    if len(units) <= 1:
        return list(units)

    if depth >= 12:
        return _sort_by_line(units, reference_height)

    gutter = _find_gutter(units, reference_height)

    if gutter is not None:

        low, high, split_x = gutter

        left = [u for u in units if u["x1"] <= split_x]
        right = [u for u in units if u["x0"] >= split_x]
        straddling = [u for u in units if u["x0"] < split_x < u["x1"]]

        settled_left, settled_right = list(left), list(right)
        spanning = []

        for unit in straddling:
            pieces = _split_unit_at_gutter(unit, low, high, split_x, left, right)
            if pieces is None:
                spanning.append(unit)
            else:
                for piece in pieces:
                    if (piece["x0"] + piece["x1"]) / 2 < split_x:
                        settled_left.append(piece)
                    else:
                        settled_right.append(piece)

        # A corridor that leaves a lot of material uncut was not a gutter.
        acceptable = max(2, int(0.2 * len(units)))

        if settled_left and settled_right and len(spanning) <= acceptable:
            return _order_columns(
                settled_left, settled_right, spanning, reference_height, depth
            )

    bands = _split_on_axis(units, "y", max(0.6 * reference_height, 2.0))

    if len(bands) > 1:
        result = []
        for band in bands:
            result.extend(_order_region(band, reference_height, depth + 1))
        return result

    return _sort_by_line(units, reference_height)


def _order_columns(left, right, spanning, reference_height, depth):
    """
    Emit two columns in reading order.

    Page spanning elements - running titles, full width headings, rules - act
    as horizontal separators: the part of both columns above one is read
    before it, and the part below after it.
    """

    if not spanning:
        return (
            _order_region(left, reference_height, depth + 1)
            + _order_region(right, reference_height, depth + 1)
        )

    separators = []
    for unit in sorted(spanning, key=lambda u: (u["y0"], u["x0"])):
        if separators and unit["y0"] <= separators[-1]["y1"]:
            separators[-1]["y0"] = min(separators[-1]["y0"], unit["y0"])
            separators[-1]["y1"] = max(separators[-1]["y1"], unit["y1"])
            separators[-1]["units"].append(unit)
        else:
            separators.append({
                "y0": unit["y0"],
                "y1": unit["y1"],
                "units": [unit]
            })

    cut_points = [(s["y0"] + s["y1"]) / 2 for s in separators]

    def into_bands(units):
        bands = [[] for _ in range(len(cut_points) + 1)]
        for unit in units:
            centre = (unit["y0"] + unit["y1"]) / 2
            index = 0
            while index < len(cut_points) and centre > cut_points[index]:
                index += 1
            bands[index].append(unit)
        return bands

    left_bands = into_bands(left)
    right_bands = into_bands(right)

    result = []
    for index in range(len(cut_points) + 1):
        for band in (left_bands[index], right_bands[index]):
            if band:
                result.extend(_order_region(band, reference_height, depth + 1))
        if index < len(cut_points):
            result.extend(
                _sort_by_line(separators[index]["units"], reference_height)
            )
    return result


def _assign_docling_regions(lines, docling_regions):
    """Tag each line with the Docling region that covers most of it."""

    for line in lines:

        line["region_key"] = None

        if not docling_regions:
            continue

        box = (line["x0"], line["y0"], line["x1"], line["y1"])
        area = max(line["x1"] - line["x0"], 1e-6) * max(line["y1"] - line["y0"], 1e-6)

        best_overlap = 0.0
        best_region = None

        for region in docling_regions:
            overlap = rectangle_overlap(box, region)
            if overlap > best_overlap:
                best_overlap = overlap
                best_region = region

        if best_region is not None and best_overlap >= 0.5 * area:
            line["region_key"] = (
                best_region["reading_order"],
                best_region["prov_index"]
            )


def _line_pitches(ordered_lines, reference_height):
    """
    Median baseline-to-baseline step, per Docling region and for the page.

    One page routinely mixes leadings - double spaced body over single spaced
    footnotes - so a single page-wide figure would be wrong for both.
    """

    page_steps = []
    region_steps = defaultdict(list)

    for previous, line in zip(ordered_lines, ordered_lines[1:]):

        step = line["y0"] - previous["y0"]
        if not 0 < step <= 4 * reference_height:
            continue

        page_steps.append(step)

        region = line["region_key"]
        if region is not None and region == previous["region_key"]:
            region_steps[region].append(step)

    # Lines cannot sit closer together than their own height; a smaller figure
    # is an artefact of superscripts and other part-height lines.
    floor = 1.05 * reference_height

    # The page-wide figure is only the fallback, for regions too short to have
    # a leading of their own, so it is taken generously: a page of single
    # spaced footnotes must not pull the body's leading down with it.
    page_steps.sort()
    page_pitch = max(
        page_steps[int(0.75 * (len(page_steps) - 1))] if page_steps
        else 1.2 * reference_height,
        floor
    )

    by_region = {
        region: max(_median(steps, default=page_pitch), floor)
        for region, steps in region_steps.items()
        if len(steps) >= 2
    }

    return by_region, page_pitch


def _group_into_paragraphs(ordered_lines, reference_height):
    """
    Merge consecutive lines of the same paragraph into one block.

    First the lines are cut into flows - runs that share a Docling region, keep
    to the body's line pitch and stay in the same column - and then each flow
    is cut wherever a line steps away from the flow's usual left edge, which is
    how a new paragraph announces itself when it is not already set off by
    extra leading.  Stepping either way counts: prose indents the first line of
    a paragraph, while numbered recitals and footnotes outdent it.
    """

    if not ordered_lines:
        return []

    pitches, page_pitch = _line_pitches(ordered_lines, reference_height)

    flows = []

    for line in ordered_lines:

        if not flows or line["block_type"] != 0 or flows[-1][-1]["block_type"] != 0:
            flows.append([line])
            continue

        previous = flows[-1][-1]

        step = line["y0"] - previous["y0"]
        overlap = min(line["x1"], previous["x1"]) - max(line["x0"], previous["x0"])
        narrower = min(line["x1"] - line["x0"], previous["x1"] - previous["x0"])

        pitch = pitches.get(line["region_key"], page_pitch)

        same_flow = (
            line["region_key"] == previous["region_key"]
            and 0 < step <= 1.4 * pitch
            and overlap >= 0.5 * max(narrower, 1e-6)
        )

        if same_flow:
            flows[-1].append(line)
        else:
            flows.append([line])

    paragraphs = []

    for flow in flows:

        # The left edge most of the lines share: continuation lines outnumber
        # paragraph openings, and ties go to the leftmost edge.
        left_counts = Counter(round(line["x0"]) for line in flow)
        left_edge = max(left_counts.items(), key=lambda item: (item[1], -item[0]))[0]

        indent = 0.5 * reference_height

        current = [flow[0]]

        for line in flow[1:]:
            if abs(line["x0"] - left_edge) > indent:
                paragraphs.append(current)
                current = [line]
            else:
                current.append(line)

        paragraphs.append(current)

    return paragraphs


def reorder_blocks_using_docling(blocks, docling_regions, group_into_paragraphs=True):
    """
    Turn the raw spans from ``get_pymupdf_lines`` into blocks in reading order.

    ``blocks``  - span tuples from ``get_pymupdf_lines``
    ``docling_regions`` - the regions of this page from ``get_docling_regions``

    Returns tuples of ``(x0, y0, x1, y1, text, block_number, block_type)`` where
    ``block_number`` is the position in reading order.
    """

    if not blocks:
        return []

    atoms = [
        {
            "x0": block[0],
            "y0": block[1],
            "x1": block[2],
            "y1": block[3],
            "text": block[4],
            "unit_number": block[5],
            "block_type": block[6],
            "line_key": block[7] if len(block) > 7 else ("text", block[5], 0)
        }
        for block in blocks
    ]

    reference_height = _line_height(atoms)

    lines = _build_lines(atoms, reference_height)
    ordered_lines = _order_region(lines, reference_height)

    # after ordering: lines that straddled a gutter have been split by then
    _assign_docling_regions(ordered_lines, docling_regions)

    if group_into_paragraphs:
        groups = _group_into_paragraphs(ordered_lines, reference_height)
    else:
        groups = [[line] for line in ordered_lines]

    reordered = []

    for block_number, group in enumerate(groups):
        reordered.append((
            min(line["x0"] for line in group),
            min(line["y0"] for line in group),
            max(line["x1"] for line in group),
            max(line["y1"] for line in group),
            "\n".join(line["text"] for line in group),
            block_number,
            group[0]["block_type"]
        ))

    return reordered


def parse_pdf_text(pdf_inputs, path_prefix = 'sources/'):
    page_rows = []
    block_rows = []
    # table_fragments = []
    pages_needing_llm = []
    
    for pdf_input in pdf_inputs:
        print(pdf_input['file_name'])
        if isinstance(pdf_input['file_name'], (str, Path)):
            source_id = Path(path_prefix + pdf_input['file_name']).stem
            doc = pymupdf.open(path_prefix + pdf_input['file_name'])
        else:
            source_id = Path(path_prefix + pdf_input['file_name'].name).stem
            doc = pymupdf.open(
                stream=(path_prefix + pdf_input['file_name']).getvalue(),
                filetype="pdf"
            )
        multiple_page_numbers = []
        active_pincite = (str(pdf_input['reporter_start_page']) if pdf_input['reporter_start_page'] is not None else None)
        docling_regions_by_page = get_docling_regions(
            file_path=path_prefix + pdf_input['file_name'],
            pymupdf_doc=doc
        )
        for page in doc:
            page_index = page.number
            docling_regions = docling_regions_by_page[page_index]
            page_display_number = page.get_label() or None
            page_text = page.get_text("text", sort=True)
            blocks = get_pymupdf_lines(page=page)
            #tables = page.find_tables().tables

            if not page_text.strip():
                ocr_textpage = page.get_textpage_ocr(language="eng", dpi=300, full=True)
                page_text = page.get_text('text', textpage = ocr_textpage, sort = True)
                blocks = get_pymupdf_lines(page=page, textpage = ocr_textpage) #to be sorted with Docling
            else:
                ocr_textpage = None

            blocks = reorder_blocks_using_docling(
                        blocks=blocks,
                        docling_regions=docling_regions
                    )

            if page_display_number is None:
                if ocr_textpage is None:
                    words = page.get_text("words", sort=True)
                else:
                    words = page.get_text("words", textpage=ocr_textpage, sort=True)
                page_height = page.rect.height
                page_width = page.rect.width
                top_limit = page_height * 0.15 #approximate margin fraction
                bottom_limit = page_height * (1 - 0.15)
                left_limit = page_width * 0.25
                right_limit = page_width * (1-0.25)
                indices_word_of = []
                indices_copyright = []
                candidates = []
                for word in words:
                    exclude = False
                    x0, y0, x1, y1, text, block_no, line_no, word_no = word
                    if (text.lower() == 'copyright') or (text.lower() == 'published') or (text.lower() == 'updated') or (text == '©'):
                        indices_copyright.append({'block': block_no, 'line': line_no, 'word': word_no})
                    cleaned_text = text.strip().strip("()[]{}.,")
                    is_arabic_number = bool(re.fullmatch(r"\d{1,4}(/\d{1,4})?('\n)*", cleaned_text))
                    is_year = cleaned_text.isdigit() and 1900 <= int(cleaned_text) <= 2100
                    previous_copyright_words = [i['word'] for i in indices_copyright if i["block"] == block_no and i["line"] == line_no  and i["word"] < word_no]
                    if is_year and previous_copyright_words:
                        most_recent_word_no = max(previous_copyright_words)
                        if word_no - most_recent_word_no < 3:
                            exclude = True
                    is_roman_number = bool(re.fullmatch(r"[ivxlcdmIVXLCDM]{1,10}",cleaned_text))
                    if text == 'of':
                        indices_word_of.append({'block': block_no, 'line': line_no, 'word': word_no})
                    at_top = y0 <= top_limit
                    if at_top & (len(candidates) > 0): 
                        highest_candidate_margin = min([c["y0"] for c in candidates])
                        if round(y0) > round(highest_candidate_margin): #below another candidate
                            at_top = False
                    at_bottom = y1 >= bottom_limit
                    if at_bottom & (len(candidates) > 0): 
                        lowest_candidate_margin = max([c["y1"] for c in candidates])
                        if round(y1) < round(lowest_candidate_margin): #above another candidate
                            at_bottom = False
                    in_corner = (x1 <= left_limit) | (x0 >= right_limit)
                    if (is_arabic_number | is_roman_number) & (at_top | at_bottom) & (not exclude):
                        candidates.append({
                            'text': cleaned_text,
                            'is_arabic': is_arabic_number,
                            'is_roman': is_roman_number,
                            'is_year': is_year,
                            'y0': y0,
                            'y1': y1,
                            'x0': x0,
                            'x1': x1,
                            'block': block_no,
                            'line': line_no,
                            'word_no': word_no,
                            'in_corner': in_corner})
                if len(candidates) > 1:
                    if len(indices_word_of) > 0:
                        precedes_of = [c for c in candidates
                                        if any(
                                            c["word_no"] + 1 == i["word"]
                                            and c["block"] == i["block"]
                                            and c["line"] == i["line"]
                                            for i in indices_word_of
                                        )]
                        for p in precedes_of:
                            word_after_of = [c for c in candidates
                                        if (c["word_no"] == p['word_no'] + 2)
                                            and (c["block"] == p["block"])
                                            and (c["line"] == p["line"])]
                            if len(word_after_of) > 0:
                                word_after_of = word_after_of[0]
                                if not word_after_of['is_arabic']:
                                    print(f"removing 'of' candidate: {p['text']}")
                                    candidates.remove(p)
                                elif (len(doc) - 2) <= int(word_after_of['text']) <= (len(doc) + 2):
                                    candidates = [p]
                                else:
                                    candidates.remove(word_after_of)
                            else:
                                print(f"removing 'of' candidate: {p['text']}")
                                candidates.remove(p)
                            
                    if len(candidates) == 1:
                        page_display_number = re.sub(r"/\d+$", "", candidates[0]['text'])
                    elif len(candidates) == 0:
                        print(f"No page number found for page index {page_index} and source {source_id}.")
                    else:
                        distances_from_edge = [min(page_height-c['y1'], c['y0']) for c in candidates]
                        smallest_distance = int(np.argmin(distances_from_edge))
                        if len([d for d in distances_from_edge if d == distances_from_edge[smallest_distance]]) == 1:
                            page_display_number = re.sub(r'/\d+$', '', candidates[smallest_distance]['text'])
                        else:
                            matches = [index for index,d in enumerate(distances_from_edge) if d == distances_from_edge[smallest_distance]]
                            candidates_in_corner = [c for c in [candidates[m] for m in matches] if c['in_corner']]
                            if len(candidates_in_corner) == 1:
                                page_display_number = re.sub(r"/\d+$", "", candidates_in_corner[0]['text'])
                            else:
                                print(f"Multiple page numbers found for page index {page_index} and source {source_id}.")
                                page_display_number = None
                                multiple_page_numbers.append(page_index)
                elif len(candidates) == 0:
                    print(f"No page number found for page index {page_index} and source {source_id}.")
                else:
                    page_display_number = re.sub(r'/\d+$', '', candidates[0]['text'])
            page_rows.append({
                'source_id': source_id,
                'page_index': page_index,
                'pdf_page_number': page_index + 1,
                'page_display_number': page_display_number,
                #'page_raw_text': "\n".join(block[4] for block in blocks)
                'page_raw_text': " ".join(
                    block[4].strip()
                    for block in blocks
                    if block[4].strip()
                )
            })
            # for table_number, table in enumerate(tables):
            #     table_fragments.append({
            #         'source_id': source_id,
            #         'page_index': page_index,
            #         'pdf_page_number': page_index + 1,
            #         'page_display_number': page_display_number,
            #         'table_number': table_number,
            #         'table_section': table.extract()
            #     })

            for reading_order, block in enumerate(blocks):
                block_text = block[4]
                pincite_matches = list(re.finditer(r'(?<!at )\*(\d+)', block_text))
                if len(pincite_matches) == 0:
                    block_rows.append({
                        'source_id': source_id,
                        'page_index': page_index,
                        'pdf_page_number': page_index + 1,
                        'page_display_number': page_display_number,
                        'block_number': block[5],
                        'full_block_number': str(page_index) + '-' + str(block[5]),
                        'block_text': block[4],
                        'block_type': 'text' if block[6] == 0 else 'image',
                        'reading_order': reading_order,
                        'x0': block[0],
                        'y0': block[1],
                        'x1': block[2],
                        'y1': block[3],
                        'first_pdf_page_number_per_source': None,
                        'reporter_start_page': pdf_input['reporter_start_page'],
                        'pincite': active_pincite
                    })
                else:
                    start = 0
                    block_segment = 0
                    for match in pincite_matches:
                        if match.start() > start:
                            block_rows.append({
                                'source_id': source_id,
                                'page_index': page_index,
                                'pdf_page_number': page_index + 1,
                                'page_display_number': page_display_number,
                                'block_number': block[5],
                                'full_block_number': str(page_index) + '-' + str(block[5]) + '-' + str(block_segment),
                                'block_text': block_text[start:match.start()],
                                'block_type': 'text' if block[6] == 0 else 'image',
                                'reading_order': reading_order,
                                'x0': block[0],
                                'y0': block[1],
                                'x1': block[2],
                                'y1': block[3],
                                'pincite': active_pincite
                            })
                        block_segment+=1
                        active_pincite = match.group(1)
                        start = match.start()
                    block_rows.append({
                        'source_id': source_id,
                        'page_index': page_index,
                        'pdf_page_number': page_index + 1,
                        'page_display_number': page_display_number,
                        'block_number': block[5],
                        'full_block_number': str(page_index) + '-' + str(block[5]) + '-' + str(block_segment),
                        'block_text': block_text[start:],
                        'block_type': 'text' if block[6] == 0 else 'image',
                        'reading_order': reading_order,
                        'x0': block[0],
                        'y0': block[1],
                        'x1': block[2],
                        'y1': block[3],
                        'first_pdf_page_number_per_source': None,
                        'reporter_start_page': pdf_input['reporter_start_page'],
                        'pincite': active_pincite
                    })

        page_length_this_source = [p for p in page_rows if p['source_id'] == source_id]


        missing_page_numbers = [p for p in page_rows if (p['source_id'] == source_id) & (pd.isna(p['page_display_number']))]
        if len(missing_page_numbers) > 0:
            print(f"{len(missing_page_numbers)} with missing display page numbers")
            for m in missing_page_numbers:
                print(f"missing page numbers for {source_id}")
                page_index_this_row = m['page_index']
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, page_index_this_row)
                if (previous_page is not None) and (next_page is not None) and (previous_page['page_display_number'] is not None) and (next_page['page_display_number'] is not None) and (str(previous_page['page_display_number']).isdigit()) and (str(next_page['page_display_number']).isdigit()) and (int(previous_page['page_display_number']) == int(next_page['page_display_number']) - 2):
                    m['page_display_number'] = str(int(previous_page['page_display_number']) + 1)
                else:
                    if (m['source_id'], m['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                        pages_needing_llm.append({
                            'source_id': source_id,
                            'page_index': this_page['page_index'],
                            'llm_page_display_number': None,
                            'this_page': this_page,
                            'previous_page': previous_page,
                            'next_page': next_page
                        })    

            missing_page_numbers_after_fix = [p for p in page_rows if (p['source_id'] == source_id) & (pd.isna(p['page_display_number']))]
            print(f"{len(missing_page_numbers_after_fix)} with missing display page numbers")
                
                         
        else:
            print("No missing page numbers.")     

        strange_page_numbers = get_strange_page_numbers(page_rows, source_id)

        if len(strange_page_numbers) > 0:
            print(f"{len(strange_page_numbers)} rows with strange page number")
            for s in strange_page_numbers:
                page_index_this_row = s['page_index']
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, page_index_this_row)
                print(f"This page: {s['page_display_number']}")
                if (previous_page is not None) and (next_page is not None):
                    previous_page_display = previous_page['page_display_number']
                    next_page_display = next_page['page_display_number']
                    print(f"Previous and next page: {previous_page_display} and {next_page_display}")
                    s['page_display_number'] = str(int(previous_page_display) + 1)
                    print(f"Changed to: {int(previous_page_display) + 1}")
                else:
                    if (this_page['source_id'], this_page['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                        pages_needing_llm.append({
                            'source_id': source_id,
                            'page_index': page_index_this_row,
                            'llm_page_display_number': None,
                            'this_page': this_page,
                            'previous_page': previous_page,
                            'next_page': next_page
                        })    

        if len(multiple_page_numbers) > 0:
            for m in multiple_page_numbers:
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, m)
                if (this_page['source_id'], this_page['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                    pages_needing_llm.append({
                        'source_id': source_id,
                        'page_index': this_page['page_index'],
                        'llm_page_display_number': None,
                        'this_page': this_page,
                        'previous_page': previous_page,
                        'next_page': next_page
                    })    
                #send LLM this page, previous page, and next page, and ask it to provide the page display number for this page.

        roman_numerals = [p for p in page_rows if (p['source_id'] == source_id) and pd.notna(p['page_display_number']) and (bool(re.fullmatch(r"[ivxlcdmIVXLCDM]{1,10}",p['page_display_number'])))]
        if len(roman_numerals) > 0:
            for r in roman_numerals:
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, r['page_index'])
                if (this_page['source_id'], this_page['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                    pages_needing_llm.append({
                        'source_id': source_id,
                        'page_index': this_page['page_index'],
                        'llm_page_display_number': None,
                        'this_page': this_page,
                        'previous_page': previous_page,
                        'next_page': next_page
                    })    

        four_digits = [p for p in page_rows if (p['source_id'] == source_id) and pd.notna(p['page_display_number']) and (len(p['page_display_number']) == 4) and (str(p['page_display_number']).isdigit())] #resembles a year
        if len(four_digits) > 0:
            for f in four_digits:
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, f['page_index'])
                if (this_page['source_id'], this_page['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                    pages_needing_llm.append({
                        'source_id': source_id,
                        'page_index': this_page['page_index'],
                        'llm_page_display_number': None,
                        'this_page': this_page,
                        'previous_page': previous_page,
                        'next_page': next_page
                    })

        #duplicate_pages
        all_page_numbers = [p['page_display_number'] for p in page_rows if (p['source_id'] == source_id) and (p['page_display_number'] is not None)]
        duplicate_page_numbers = {page_number for page_number in all_page_numbers if all_page_numbers.count(page_number) > 1 }
        if len(duplicate_page_numbers) > 0:
            pages_with_duplicate_page_numbers = [p for p in page_rows if (p['source_id'] == source_id) and (p['page_display_number'] in duplicate_page_numbers)]
            for d in pages_with_duplicate_page_numbers:
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, d['page_index'])               
                if (this_page['source_id'], this_page['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                    pages_needing_llm.append({
                        'source_id': source_id,
                        'page_index': this_page['page_index'],
                        'llm_page_display_number': None,
                        'this_page': this_page,
                        'previous_page': previous_page,
                        'next_page': next_page
                    })

        source_rows = sorted([p for p in page_rows if p['source_id'] == source_id],
                             key=lambda x: x['page_index'])

        for previous, current in zip(source_rows, source_rows[1:]):
            previous_display = previous['page_display_number']
            current_display = current['page_display_number']

            if (pd.notna(previous_display) and pd.notna(current_display)  and str(previous_display).isdigit() and str(current_display).isdigit() and int(current_display) != int(previous_display) + 1):
                this_page, previous_page, next_page = get_neighboring_pages(source_id, page_rows, current['page_index'])               
                if (this_page['source_id'], this_page['page_index']) not in [(p['source_id'], p['page_index']) for p in pages_needing_llm]:
                    pages_needing_llm.append({
                        'source_id': source_id,
                        'page_index': this_page['page_index'],
                        'llm_page_display_number': None,
                        'this_page': this_page,
                        'previous_page': previous_page,
                        'next_page': next_page
                    })


    fixed_page_numbers =  llm_page_number_verification(pages_needing_llm)
    for f in fixed_page_numbers:
        if f['this_page']['page_display_number'] != f['llm_page_display_number']:
            f['this_page']['page_display_number'] = f['llm_page_display_number']
            relevant_blocks = [
                b for b in block_rows
                if (b['source_id'] == f['source_id'])
                and (b['page_index'] == f['page_index'])
            ]
            for rb in relevant_blocks:
                rb['page_display_number'] = f['llm_page_display_number']


    first_pdf_page_number_per_source = { p['source_id']: p['page_display_number'] for p in page_rows if p['page_index'] == 0}
    for b in block_rows:
        b['first_pdf_page_number_per_source'] = first_pdf_page_number_per_source[b['source_id']]

    for pdf_input in pdf_inputs:
        source_id = Path(pdf_input['file_name']).stem
        blocks_this_source = [b for b in block_rows if b['source_id'] == source_id]
        # Inline pincites were already assigned during parsing.
        if any(re.search(r'(?<!at )\*(\d+)', b['block_text']) for b in blocks_this_source):
            continue
        reporter_start_page = pdf_input['reporter_start_page']
        first_display_page = first_pdf_page_number_per_source[source_id]
        for b in blocks_this_source:
            if reporter_start_page is None:
                b['pincite'] = b['page_display_number']
            elif first_display_page is not None and str(first_display_page).isdigit() and int(first_display_page) == int(reporter_start_page):
                # National Cycle: displayed page already IS reporter page.
                b['pincite'] = b['page_display_number']
            else:
                # PDF pages numbered 1,2,3... but reporter starts elsewhere.
                page_number = b['page_display_number'] if b['page_display_number'] is not None else b['pdf_page_number']
                b['pincite'] = int(reporter_start_page) + int(page_number) - 1


    # new_table_fragments = []
    # for table_source in np.unique([table['source_id'] for table in table_fragments]):
    #     table_groups = []
    #     tables_this_source = [tab for tab in table_fragments if tab['source_id'] == table_source]
    #     page_numbers_with_tables =  np.unique([tab['page_index'] for tab in tables_this_source])
    #     for value in page_numbers_with_tables:
    #         this_page, previous_page, next_page = get_neighboring_pages(table_source, page_rows, value)                 
    #         if not table_groups or value != table_groups[-1][-1] + 1:
    #             table_groups.append([value])
    #         else:
    #             table_groups[-1].append(value)
    #     for g in table_groups:
    #         tables_in_this_group = [tab for tab in tables_this_source if tab['page_index'] in g]
    #         combined_table_text = []
    #         for tab in tables_in_this_group:
    #             combined_table_text.append(tab['table_section'])
    #         for tab in tables_in_this_group:
    #             tab['table_text'] = combined_table_text
    #             tab['page_numbers'] = g
    #             #send to llm: this page, previous_page, next_page, tab,  and ask if tab is actually a table.
    #             #if llm says it is a table:
    #             new_table_fragments.append(tab)

    

    # for page in [p for p in page_rows if p['source_id'] == source_id]:
    #     for block in block_rows:
    #         if (block['source_id'] == source_id and block['page_index'] == page['page_index']):
    #             block['page_display_number'] = page['page_display_number']
    #     for table in table_fragments:
    #         if (table['source_id'] == source_id and table['page_index'] == page['page_index']):
    #             table['page_display_number'] = page['page_display_number']

    


    return [page_rows, block_rows]

#%%
