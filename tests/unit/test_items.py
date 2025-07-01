"""Unit tests for items module."""

import pytest
from policy_enforcer.items import Item, ItemRequirements


class TestItem:
    """Test Item enum."""
    
    def test_item_values(self):
        """Test Item enum has correct values."""
        assert Item.TV.value == "TV"
        assert Item.XBOX.value == "Xbox"
        assert Item.HIKING_BOOTS.value == "Hiking Boots"
        assert Item.GOGGLES.value == "Goggles"
        assert Item.SUNSCREEN.value == "Sunscreen"
    
class TestItemRequirements:
    """Test ItemRequirements class."""

    def test_normalize_item_name(self):
        """Test item name normalization."""
        assert ItemRequirements.normalize_item_name("tv") == "TV"
        assert ItemRequirements.normalize_item_name("TV") == "TV"
        assert ItemRequirements.normalize_item_name("xbox") == "Xbox"
        assert ItemRequirements.normalize_item_name("XBOX") == "Xbox"
        assert ItemRequirements.normalize_item_name("hiking boots") == "Hiking Boots"
        assert ItemRequirements.normalize_item_name("HIKING BOOTS") == "Hiking Boots"
        assert ItemRequirements.normalize_item_name("goggles") == "Goggles"
        assert ItemRequirements.normalize_item_name("sunscreen") == "Sunscreen"
    
    def test_normalize_item_name_invalid(self):
        """Test normalization of invalid item names."""
        assert ItemRequirements.normalize_item_name("invalid") == "invalid"  # Returns original
        assert ItemRequirements.normalize_item_name("") == ""
    
    def test_is_valid_item(self):
        """Test item validation."""
        # Valid items
        assert ItemRequirements.is_valid_item("TV")
        assert ItemRequirements.is_valid_item("tv")
        assert ItemRequirements.is_valid_item("Xbox")
        assert ItemRequirements.is_valid_item("xbox")
        assert ItemRequirements.is_valid_item("Hiking Boots")
        assert ItemRequirements.is_valid_item("hiking boots")
        assert ItemRequirements.is_valid_item("HIKING BOOTS")
        assert ItemRequirements.is_valid_item("Goggles")
        assert ItemRequirements.is_valid_item("goggles")
        assert ItemRequirements.is_valid_item("Sunscreen")
        assert ItemRequirements.is_valid_item("sunscreen")
        
        # Invalid items
        assert not ItemRequirements.is_valid_item("invalid")
        assert not ItemRequirements.is_valid_item("")
        assert not ItemRequirements.is_valid_item(None)
        assert not ItemRequirements.is_valid_item("NonExistent")
    
    def test_get_all_items(self):
        """Test getting all available items."""
        items = ItemRequirements.get_all_items()
        expected = ["TV", "Xbox", "Hiking Boots", "Goggles", "Sunscreen"]
        assert items == expected
    
    def test_get_requirements_for_activity(self):
        """Test getting requirements for activities."""
        gaming_reqs = ItemRequirements.get_requirements_for_activity("Play games")
        assert Item.TV in gaming_reqs
        assert Item.XBOX in gaming_reqs
        
        camping_reqs = ItemRequirements.get_requirements_for_activity("Go Camping")
        assert Item.HIKING_BOOTS in camping_reqs
        
        swimming_reqs = ItemRequirements.get_requirements_for_activity("Swimming")
        assert Item.GOGGLES in swimming_reqs
    
    def test_get_missing_items(self):
        """Test getting missing items for activities."""
        # Empty inventory
        missing = ItemRequirements.get_missing_items("Play games", set())
        assert len(missing) == 2
        assert Item.TV in missing
        assert Item.XBOX in missing
        
        # Partial inventory
        missing = ItemRequirements.get_missing_items("Play games", {"TV"})
        assert len(missing) == 1
        assert Item.XBOX in missing
        
        # Complete inventory
        missing = ItemRequirements.get_missing_items("Play games", {"TV", "Xbox"})
        assert len(missing) == 0