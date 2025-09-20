# CineAnalytics-Inc
CineAnalytics Inc. is a film industry analytics company. We collect and analyze data on films, actors, genres, and ratings from IMDb. Our primary goal is to identify film trends, popular genres, successful actors and directors, and ratings trends over the years.
```mermaid
erDiagram
    NAME_BASICS {
        string nconst PK
        string primaryName
        int birthYear
        int deathYear
        string primaryProfession
        string knownForTitles
    }

    TITLE_BASICS {
        string tconst PK
        string titleType
        string primaryTitle
        string originalTitle
        boolean isAdult
        int startYear
        int endYear
        int runtimeMinutes
        string genres
    }

    TITLE_RATINGS {
        string tconst PK
        float averageRating
        int numVotes
    }

    TITLE_CREW {
        string tconst PK
        string directors
        string writers
    }

    TITLE_PRINCIPALS {
        string tconst
        int ordering
        string nconst
        string category
        string job
        string characters
        PK(tconst, ordering, nconst)
    }

    TITLE_EPISODE {
        string tconst PK
        string parentTconst
        int seasonNumber
        int episodeNumber
    }

    TITLE_AKAS {
        string titleId
        int ordering
        string title
        string region
        string language
        string types
        string attributes
        boolean isOriginalTitle
        PK(titleId, ordering)
    }

    TITLE_BASICS ||--o{ TITLE_RATINGS : "has"
    TITLE_BASICS ||--o{ TITLE_CREW : "has"
    TITLE_BASICS ||--o{ TITLE_PRINCIPALS : "has"
    TITLE_BASICS ||--o{ TITLE_EPISODE : "parent of"
    TITLE_BASICS ||--o{ TITLE_AKAS : "alias"
    TITLE_PRINCIPALS }|..|{ NAME_BASICS : "who"
