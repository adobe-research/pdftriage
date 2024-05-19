
def compose(list_of_functions_with_arguments: list[tuple]) -> str:
    """Compose a list of functions with arguments.
    It is used when a combination of functions is needed, or additional information is needed which one function cannot provide by itself.
    
    Functions available for compositions are search_document, fetch_pages, fetch_section, and fetch_all.
    
    search_document takes a search term as an argument. It is used when a simple search is needed, for example, for fact or knowledge based questions.
    fetch_pages takes a list of page numbers as an argument. It is used when a specific page is needed.
    fetch_section takes a section title as an argument. It is used when a specific section is needed, for example, for deeper understanding of a topic.

    ALWAYS call search_document. It is the most important function.

    Args:
        list_of_functions_with_arguments: A list of tuples of functions and arguments.
    """
    return f"compose_helper will be called"

def fetch_pages(page_numbers: list[int]) -> str:
    """Fetch the content of specified pages from the document.
    It is used when a specific page is needed.

    Args:
        page_numbers: The list of pages to fetch.
    """
    return f"fetch_pages_helper will be called"

def fetch_section(section_title: str, section_id: int) -> str:
    """Fetch the content of specified section from the document.
    It is used when a specific section is needed, for example, for deeper understanding of a topic.
    It is MANDATORY to call this function with the exact section title as it appears in TABLE_OF_CONTENTS.

    Args:
        section: The title of section to fetch.
    """
    return f"fetch_section_helper will be called"

def fetch_all() -> str:
    """Fetch the content of the entire document.
    It is used when the entire document is needed, for example, for summarization.
    """
    return f"fetch_all_helper will be called"

def search_document(query: str) -> str:
    """Search the document for a string query. 
    It is used when a simple search is needed, for example, for fact or knowledge based questions.

    Args:
        query: The search term
    """
    return f"search_index_default will be called"
