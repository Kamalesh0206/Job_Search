import re


def normalize(text):

    text = (
        text or ""
    ).lower()

    text = re.sub(
        r"[\u2013\u2014/_|(),:]+",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def contains_any(
    text,
    terms
):

    text = normalize(
        text
    )

    for term in terms:

        term_n = normalize(
            term
        )

        if term_n in text:
            return True

    return False


def count_terms(
    text,
    terms
):

    text = normalize(
        text
    )

    count = 0

    for term in terms:

        if normalize(
            term
        ) in text:

            count += 1

    return count


def classify_job(
    title,
    description,
    config
):

    title_n = normalize(
        title
    )

    desc_n = normalize(
        description
    )

    combined = (
        title_n
        + " "
        + desc_n
    )

    # ---------------------------------
    # STEP 1
    # Reject clearly irrelevant titles
    # ---------------------------------

    if contains_any(
        title_n,
        config.get(
            "exclude_title_terms",
            []
        )
    ):
        return None


    # ---------------------------------
    # STEP 2
    # AI Product Manager
    # Most specific PM classification
    # ---------------------------------

    ai_pm_titles = (
        config[
            "role_families"
        ][
            "AI Product Manager"
        ][
            "title_terms"
        ]
    )

    if contains_any(
        title_n,
        ai_pm_titles
    ):
        return (
            "AI Product Manager"
        )


    # ---------------------------------
    # STEP 3
    # AI Engineer
    # ---------------------------------

    ai_eng_titles = (
        config[
            "role_families"
        ][
            "Senior AI Software Engineer"
        ][
            "title_terms"
        ]
    )

    if contains_any(
        title_n,
        ai_eng_titles
    ):
        return (
            "Senior AI Software Engineer"
        )


    # ---------------------------------
    # STEP 4
    # Technical Product Manager
    # ---------------------------------

    tech_pm_titles = (
        config[
            "role_families"
        ][
            "Technical Product Manager"
        ][
            "title_terms"
        ]
    )

    if contains_any(
        title_n,
        tech_pm_titles
    ):

        # Generic Product Manager
        # may actually be AI PM.

        if (
            "product manager"
            in title_n
        ):

            ai_hits = count_terms(
                combined,
                config.get(
                    "ai_context_terms",
                    []
                )
            )

            if ai_hits >= 2:

                return (
                    "AI Product Manager"
                )

        return (
            "Technical Product Manager"
        )


    # ---------------------------------
    # STEP 5
    # Senior Software Engineer
    # ---------------------------------

    software_titles = (
        config[
            "role_families"
        ][
            "Senior Software Engineer"
        ][
            "title_terms"
        ]
    )

    if contains_any(
        title_n,
        software_titles
    ):
        return (
            "Senior Software Engineer"
        )


    # ---------------------------------
    # Nothing matched
    # ---------------------------------

    return None