from analyzer.parser import DeckEntry, ParsedDeck, apply_commander_override, parse_decklist


def test_basic_quantity_and_name():
    deck = parse_decklist("1 Sol Ring\n2 Forest")
    assert deck.cards == [
        DeckEntry(quantity=1, name="Sol Ring"),
        DeckEntry(quantity=2, name="Forest"),
    ]
    assert deck.commanders == []


def test_ignores_blank_lines_and_comments():
    text = """
    # comentario
    1 Sol Ring

    // otro comentario
    1 Arcane Signet
    """
    deck = parse_decklist(text)
    assert [c.name for c in deck.cards] == ["Sol Ring", "Arcane Signet"]


def test_commander_section_header():
    text = """
    Commander:
    1 Atraxa, Praetors' Voice

    Deck:
    1 Sol Ring
    1 Command Tower
    """
    deck = parse_decklist(text)
    assert deck.commanders == ["Atraxa, Praetors' Voice"]
    assert [c.name for c in deck.cards] == ["Sol Ring", "Command Tower"]


def test_inline_commander_tag():
    text = "1 Atraxa, Praetors' Voice *CMDR*\n1 Sol Ring"
    deck = parse_decklist(text)
    assert deck.commanders == ["Atraxa, Praetors' Voice"]
    assert [c.name for c in deck.cards] == ["Sol Ring"]


def test_maybeboard_and_sideboard_are_skipped():
    text = """
    Deck:
    1 Sol Ring

    Maybeboard:
    1 Cyclonic Rift
    """
    deck = parse_decklist(text)
    assert [c.name for c in deck.cards] == ["Sol Ring"]


def test_strips_set_and_collector_number_and_foil_tag():
    deck = parse_decklist("1 Arid Mesa (MH2) 123 *F*")
    assert deck.cards == [DeckEntry(quantity=1, name="Arid Mesa")]


def test_quantity_with_x_suffix():
    deck = parse_decklist("1x Sol Ring")
    assert deck.cards == [DeckEntry(quantity=1, name="Sol Ring")]


def test_apply_commander_override_adds_name_when_missing():
    deck = ParsedDeck(commanders=[], cards=[DeckEntry(quantity=1, name="Sol Ring")])
    apply_commander_override(deck, "Sythis, Harvest's Hand")
    assert deck.commanders == ["Sythis, Harvest's Hand"]


def test_apply_commander_override_does_not_duplicate_existing_commander():
    deck = ParsedDeck(commanders=["Sythis, Harvest's Hand"], cards=[])
    apply_commander_override(deck, "sythis, harvest's hand")
    assert deck.commanders == ["Sythis, Harvest's Hand"]


def test_apply_commander_override_ignores_blank_or_none():
    deck = ParsedDeck(commanders=[], cards=[])
    apply_commander_override(deck, None)
    apply_commander_override(deck, "   ")
    assert deck.commanders == []
