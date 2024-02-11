def sources_to_text(sources):
    """Convert a list of sources to a string."""
    if not sources:
        return ""
    return "\nSource documents:\n" + "\n".join(
        f"- {source.metadata['title']} ({source.metadata['source']}, chunk {source.metadata['chunk']})"
        for source in sources
    )


def sources_to_md(sources):
    """Convert a list of sources to a Markdown string."""
    if not sources:
        return ""
    sources = {
        source.metadata["source"]: source.metadata["title"] for source in sources
    }
    return "\n**Source documents:**\n" + "\n".join(
        f"- [{title}]({url})" for url, title in sources.items()
    )
