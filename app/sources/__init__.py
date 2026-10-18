from dataclasses import dataclass, field


@dataclass
class Alias:
    name: str
    lang: str = ""
    quality: str = "strong"   # primary | strong | weak


@dataclass
class Entry:
    source: str
    source_id: str
    entity_type: str
    primary_name: str
    aliases: list = field(default_factory=list)          # list[Alias]
    birth_dates: list = field(default_factory=list)      # list[dict]
    nationalities: list = field(default_factory=list)    # list[{iso2, name}]
    programs: list = field(default_factory=list)
    listed_on: str = ""
    url: str = ""
    remarks: str = ""
    extra: dict = field(default_factory=dict)


@dataclass
class ParseResult:
    entries: list
    list_date: str
