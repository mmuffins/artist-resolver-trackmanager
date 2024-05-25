import pytest
import httpx
import respx
import json
from artist_resolver.trackmanager import (
    MbArtistDetails,
    TrackManager,
)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_mbartist_objects_without_db_information(respx_mock):
    # Arrange
    manager = TrackManager()

    artist1 = MbArtistDetails(
        name="Artist1",
        type="Person",
        disambiguation="",
        sort_name="Artist1, Firstname",
        id="mock-artist1-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist2 = MbArtistDetails(
        name="Artist2",
        type="Person",
        disambiguation="",
        sort_name="Artist2, Firstname",
        id="mock-artist2-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    # Populate artist_data with MbArtistDetails
    manager.artist_data[artist1.mbid] = artist1
    manager.artist_data[artist2.mbid] = artist2

    # Mock the DB call to always return 404
    respx_mock.route(
        method="GET",
        port__in=[manager.api_port],
        host=manager.api_host,
        path__regex=r"/api/mbartist/mbid/.*",
    ).mock(return_value=httpx.Response(404))

    # Add a catch-all for everything that's not explicitly routed
    # respx_mock.route().respond(404)

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert manager.artist_data[artist1.mbid].custom_name == artist1.sort_name
    assert manager.artist_data[artist2.mbid].custom_name == artist2.sort_name
    assert manager.artist_data[artist1.mbid].custom_original_name == artist1.name
    assert manager.artist_data[artist2.mbid].custom_original_name == artist2.name
    assert manager.artist_data[artist1.mbid].include == artist1.include
    assert manager.artist_data[artist2.mbid].include == artist2.include


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_create_mbartist_objects_with_db_information(respx_mock):
    # Arrange
    manager = TrackManager()

    artist1 = MbArtistDetails(
        name="Artist1 Lastname",
        type="Person",
        disambiguation="",
        sort_name="Lastname, Artist1",
        id="mock-artist1-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist1_expected = {
        "id": 239,
        "mbid": "mock-artist1-id",
        "custom_name": "Expected Lastname Artist1",
        "custom_original_name": "Expected Lastname Artist1 Original",
        "include": False,
    }

    # Populate artist_data with MbArtistDetails
    manager.artist_data[artist1.mbid] = artist1

    # Mock the DB call to return 200 for the specified mbid
    respx_mock.route(
        method="GET",
        port__in=[manager.api_port],
        host=manager.api_host,
        path=f"/api/mbartist/mbid/mock-artist1-id",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist1_expected["id"],
                "mbid": artist1_expected["mbid"],
                "name": artist1_expected["custom_name"],
                "originalName": artist1_expected["custom_original_name"],
                "include": artist1_expected["include"],
            },
        )
    )

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert manager.artist_data[artist1.mbid].id == artist1_expected["id"]
    assert manager.artist_data[artist1.mbid].mbid == artist1_expected["mbid"]
    assert (
        manager.artist_data[artist1.mbid].custom_name == artist1_expected["custom_name"]
    )
    assert (
        manager.artist_data[artist1.mbid].custom_original_name
        == artist1_expected["custom_original_name"]
    )
    assert manager.artist_data[artist1.mbid].include == artist1_expected["include"]


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_mbid_not_found_in_db_when_saving(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_id = 35

    artist = MbArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist.mbid = "mock-artist1-id"
    artist.include = False
    artist.custom_name = "New custom name"
    artist.custom_original_name = "New custom original name"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(return_value=httpx.Response(404))

    # Mock call to update artist
    respx_mock.route(
        method="POST",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "mbId": artist.mbid,
                "name": artist.custom_name,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Act
    await manager.send_mbartist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 2

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"

    # post new artist
    assert (
        respx_mock.calls[1].request.method == "POST"
    ), "Call to update artist was not of type UPDATE"
    call_1_content = json.loads(respx_mock.calls[1].request.content.decode())
    assert call_1_content == {
        "MbId": artist.mbid,
        "Name": artist.custom_name,
        "OriginalName": artist.custom_original_name,
        "Include": artist.include,
    }, f"Post body to update artist did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_mbid_found_on_server_when_saving_data_identical(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_name = "New custom name"
    server_artist_id = 35

    artist = MbArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist.mbid = "mock-artist1-id"
    artist.include = True
    artist.custom_name = server_artist_name
    artist.custom_original_name = "New custom original name"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "mbId": artist.mbid,
                "name": server_artist_name,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Act
    await manager.send_mbartist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 1

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_mbid_found_on_server_when_saving_data_changed(respx_mock):
    # Arrange
    manager = TrackManager()

    server_artist_name = "ServerCustomName"
    server_artist_id = 35

    artist = MbArtistDetails(
        name="NewSimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="NewSimpleArtist",
        id=None,
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    artist.mbid = "mock-artist1-id"
    artist.include = True
    artist.custom_name = "New custom name"
    artist.custom_original_name = "New custom original name"
    manager.artist_data[artist.mbid] = artist

    # Mock first request to not return anything when checking artist by name
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": server_artist_id,
                "mbId": artist.mbid,
                "name": server_artist_name,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Mock call to update artist
    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/id/{server_artist_id}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist.id,
                "mbId": artist.mbid,
                "name": artist.custom_name,
                "originalName": artist.custom_original_name,
                "include": artist.include,
            },
        )
    )

    # Act
    await manager.send_mbartist_changes_to_db(artist)

    # Assert
    assert respx_mock.calls.call_count == 2

    # verify if artist exists
    assert (
        respx_mock.calls[0].request.method == "GET"
    ), "Call to verify if an artist exist was not of type GET"

    # post new artist
    assert (
        respx_mock.calls[1].request.method == "PUT"
    ), "Call to update artist was not of type UPDATE"
    call_1_content = json.loads(respx_mock.calls[1].request.content.decode())
    assert call_1_content == {
        "MbId": artist.mbid,
        "Name": artist.custom_name,
        "OriginalName": artist.custom_original_name,
        "Include": artist.include,
    }, f"Post body to update artist did not match expected object"


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_from_customization_sets_updated_from_server(respx_mock):
    # Arrange
    manager = TrackManager()

    artist = MbArtistDetails(
        name="MbArtist",
        type="Person",
        disambiguation="",
        sort_name="MbArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
    )

    manager.artist_data[artist.mbid] = artist

    # Mock the DB call to return artist data
    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{artist.mbid}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 1,
                "mbid": "mock-artist-id",
                "name": "UpdatedMbArtist",
                "originalName": "MbArtist",
                "include": True,
            },
        )
    )

    # Act
    await manager.update_artists_info_from_db()

    # Assert
    assert artist.updated_from_server, "Expected artist.updated_from_server to be True"
