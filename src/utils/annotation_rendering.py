from collections import defaultdict


def get_sections_and_text(chunks):
    text = "".join(chunk["page_content"] for chunk in chunks["chunks"])
    sections = [
        {
            "start": chunk["metadata"]["start_index"],
            "end": chunk["metadata"]["start_index"] + len(chunk["page_content"]),
            "text": chunk["page_content"],
        }
        for chunk in chunks["chunks"]
    ]
    return sections, text


def calculate_coverage(selection):
    coverage = defaultdict(int)
    for s in selection:
        for i in range(s["start"], s["end"]):
            coverage[i] += 1
    return coverage


def create_end_markers(selection):
    end_markers = defaultdict(list)
    for i, s in enumerate(selection, 1):
        end_markers[s["end"]].append(i)
    return end_markers


def highlight_text(text, coverage, end_markers):
    output = []
    buffer = []

    def flush_buffer():
        if buffer:
            output.append("".join(buffer))
            buffer.clear()

    for i, ch in enumerate(text):
        if coverage.get(i, 0) > 0:
            # flush normal markdown
            flush_buffer()

            opacity = min(0.3 + 0.2 * coverage[i], 0.8)
            output.append(
                f"<span style='background: rgba(255, 230, 150, {opacity});'>"
                f"{ch}</span>"
            )
        else:
            buffer.append(ch)

        if i + 1 in end_markers:
            flush_buffer()
            if ch.isalnum():
                output.append(" ")
            for m in end_markers[i + 1]:
                output.append(f"[^{m}]")

    flush_buffer()
    return "".join(output)


def create_layout(annotated_text, sections):
    annotations = []
    for i, s in enumerate(sections, 1):
        annotations.append(f"[^{i}]: Section {i} {s['rebuttal']}")

    markdown = (
        f"{annotated_text}\n\n" f"---\n\n" f"### Annotations\n" + "\n".join(annotations)
    )

    return markdown


def render_annotated_text(chunks):
    sections, text = get_sections_and_text(chunks)
    coverage = calculate_coverage(sections)
    end_markers = create_end_markers(sections)
    annotated_text = highlight_text(text, coverage, end_markers)
    layout = create_layout(annotated_text, sections)
    return layout
