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
        string tconst PK, FK
        float averageRating
        int numVotes
    }
    TITLE_PRINCIPALS {
        string tconst FK
        int ordering
        string nconst FK
        string category
        string job
        string characters
    }
    TITLE_AKAS {
        string titleId FK
        int ordering
        string title
        string region
        string language
        string types
        string attributes
        boolean isOriginalTitle
    }

    TITLE_BASICS ||--o{ TITLE_RATINGS : "rated by"
    TITLE_BASICS ||--o{ TITLE_PRINCIPALS : "has principals"
    TITLE_BASICS ||--o{ TITLE_AKAS : "alias"
    TITLE_PRINCIPALS }|..|{ NAME_BASICS : "who"


    TITLE_BASICS ||--o{ TITLE_RATINGS : "rated by"
    TITLE_BASICS ||--o{ TITLE_PRINCIPALS : "has principals"
    TITLE_BASICS ||--o{ TITLE_AKAS : "has alias"
    TITLE_PRINCIPALS }|..|{ NAME_BASICS : "who"
