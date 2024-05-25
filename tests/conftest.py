import pytest
from unittest.mock import MagicMock
from mutagen.id3 import TIT2, TPE1, TALB, TPE2, TIT1, TOAL, TOPE, TPE3


@pytest.fixture
def mock_id3_instance(mocker):
    """
    Fixture that returns a mocked mutagen id3 instance
    """

    mocked_id3 = mocker.patch("mutagen.id3.ID3", autospec=True)
    mock_id3_instance = MagicMock()
    mocked_id3.return_value = mock_id3_instance
    # Mock the main get_id3_object call to get a dummy object
    mocker.patch(
        "artist_resolver.trackmanager.TrackDetails.get_id3_object", return_value=mock_id3_instance
    )
    return mock_id3_instance


class MockID3Tag:
    def __init__(self, text):
        self.text = text


@pytest.fixture
def mock_id3_tags(mock_id3_instance):
    """
    A fixture to configure mock ID3 tags on a provided mock ID3 instance.
    """

    def apply_mock(tags):

        def id3_get_side_effect(tag):
            value = tags.get(tag)
            if isinstance(value, (TIT2, TPE1, TALB, TPE2, TIT1, TOAL, TOPE, TPE3)):
                return value
            else:
                return MockID3Tag(value)

        mock_id3_instance.get.side_effect = id3_get_side_effect
        return mock_id3_instance

    return apply_mock
