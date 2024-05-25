import pytest
import httpx
import respx
from TrackManager import (
    TrackManager,
    MbArtistDetails,
    SimpleArtistDetails,
)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_post_simple_artist_success(respx_mock):
    # Arrange
    manager = TrackManager()

    artist = SimpleArtistDetails(
        name="SimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    respx_mock.route(
        method="POST",
        port=manager.API_PORT,
        host=manager.API_DOMAIN,
        path="/api/artist",
    ).mock(
        return_value=httpx.Response(
            200, json={"id": 99, "name": "SimpleArtist", "aliases": []}
        )
    )

    # Act
    await manager.post_simple_artist(artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to post the artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_post_simple_artist_conflict(respx_mock):
    # Arrange
    manager = TrackManager()

    artist = SimpleArtistDetails(
        name="SimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )

    respx_mock.route(
        method="POST", port=manager.api_port, host=manager.api_host, path="/api/artist"
    ).mock(return_value=httpx.Response(409))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.post_simple_artist(artist)
    assert "Failed to post artist data" in str(excinfo.value)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_post_simple_artist_alias_success(respx_mock):
    # Arrange
    manager = TrackManager()

    artist_id = 1
    name = "SimpleArtistAlias"
    franchise_id = 1

    respx_mock.route(
        method="POST", port=manager.api_port, host=manager.api_host, path="/api/alias"
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": 88,
                "name": "SimpleArtistAlias",
                "artistId": 99,
                "artist": "SimpleArtist",
                "franchiseId": 4,
                "franchise": "TestProduct",
            },
        )
    )

    # Act
    await manager.post_simple_artist_alias(artist_id, name, franchise_id)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to post the artist alias, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_post_simple_artist_alias_conflict(respx_mock):
    # Arrange
    manager = TrackManager()
    artist_id = 1
    name = "SimpleArtistAlias"
    franchise_id = 1

    respx_mock.route(
        method="POST", port=manager.api_port, host=manager.api_host, path="/api/alias"
    ).mock(return_value=httpx.Response(409))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.post_simple_artist_alias(artist_id, name, franchise_id)
    assert "Alias with name" in str(excinfo.value)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_delete_simple_artist_alias_success(respx_mock):
    # Arrange
    manager = TrackManager()
    alias_id = 88

    respx_mock.route(
        method="DELETE",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/alias/id/{alias_id}",
    ).mock(return_value=httpx.Response(200))

    # Act
    await manager.delete_simple_artist_alias(alias_id)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to delete the alias, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_delete_simple_artist_alias_not_found(respx_mock):
    # Arrange
    manager = TrackManager()
    alias_id = 88

    respx_mock.route(
        method="DELETE",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/alias/id/{alias_id}",
    ).mock(return_value=httpx.Response(404))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.delete_simple_artist_alias(alias_id)
    assert f"Alias with ID {alias_id} was not found" in str(excinfo.value)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_delete_simple_artist_alias_server_error(respx_mock):
    # Arrange
    manager = TrackManager()
    alias_id = 88

    respx_mock.route(
        method="DELETE",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/alias/id/{alias_id}",
    ).mock(return_value=httpx.Response(500))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.delete_simple_artist_alias(alias_id)
    assert f"An error occurred when deleting alias with ID {alias_id}" in str(
        excinfo.value
    )


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_simple_artist_success(respx_mock):
    # Arrange
    manager = TrackManager()
    artist = SimpleArtistDetails(
        name="SimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )
    artist.custom_name = "New Custom Name"
    artist_id = 1

    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/artist/id/{artist_id}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist_id,
                "name": artist.custom_name,
                "aliases": [],
            },
        )
    )

    # Act
    await manager.update_simple_artist(artist_id, artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to update the artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_simple_artist_not_found(respx_mock):
    # Arrange
    manager = TrackManager()
    artist = SimpleArtistDetails(
        name="SimpleArtist",
        type="Person",
        disambiguation="",
        sort_name="SimpleArtist",
        id="mock-artist-id",
        aliases=[],
        type_id="b6e035f4-3ce9-331c-97df-83397230b0df",
        joinphrase="",
        product="TestProduct",
        product_id="1",
    )
    artist_id = 1

    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/artist/id/{artist_id}",
    ).mock(return_value=httpx.Response(404))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.update_simple_artist(artist_id, artist)
    assert "Could not find artist with MBID" in str(excinfo.value)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_simple_artist_success(respx_mock):
    # Arrange
    manager = TrackManager()
    artist_id = 99
    name = "SimpleArtist"

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={"id": artist_id, "name": name},
    ).mock(
        return_value=httpx.Response(
            200, json=[{"id": artist_id, "name": name, "aliases": []}]
        )
    )

    # Act
    result = (await manager.get_simple_artist(artist_id, name))[0]

    # Assert
    assert result["id"] == artist_id
    assert result["name"] == name
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to get the artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_simple_artist_not_found(respx_mock):
    # Arrange
    manager = TrackManager()
    artist_id = 99
    name = "SimpleArtist"

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/artist",
        params={"id": artist_id, "name": name},
    ).mock(return_value=httpx.Response(200, json=[]))

    # Act
    result = await manager.get_simple_artist(artist_id, name)

    # Assert
    assert result is None
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to get the artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_simple_artist_alias_success(respx_mock):
    # Arrange
    manager = TrackManager()
    name = "SimpleArtist"
    franchise_id = 4

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": name, "franchiseId": franchise_id},
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 88,
                    "name": name,
                    "artistId": 99,
                    "artist": "SimpleArtist",
                    "franchiseId": franchise_id,
                    "franchise": "TestProduct",
                }
            ],
        )
    )

    # Act
    result = await manager.get_simple_artist_alias(name, franchise_id)

    # Assert
    assert result[0]["name"] == name
    assert result[0]["franchiseId"] == franchise_id
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to get the artist alias, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_simple_artist_alias_not_found(respx_mock):
    # Arrange
    manager = TrackManager()
    name = "SimpleArtist"
    franchise_id = 4

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/alias",
        params={"name": name, "franchiseId": franchise_id},
    ).mock(return_value=httpx.Response(200, json=[]))

    # Act
    result = await manager.get_simple_artist_alias(name, franchise_id)

    # Assert
    assert result is None
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to get the artist alias, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_mbartist_success(respx_mock):
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
    artist.custom_name = "New Custom Name"
    artist_id = 1

    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/id/{artist_id}",
    ).mock(
        return_value=httpx.Response(
            200,
            json={
                "id": artist_id,
                "name": artist.custom_name,
                "aliases": [],
            },
        )
    )

    # Act
    await manager.update_mbartist(artist_id, artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to update the MB artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_update_mbartist_not_found(respx_mock):
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
    artist_id = 1

    respx_mock.route(
        method="PUT",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/id/{artist_id}",
    ).mock(return_value=httpx.Response(404))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.update_mbartist(artist_id, artist)
    assert "Could not find artist with MBID" in str(excinfo.value)


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_mbartist_success(respx_mock):
    # Arrange
    manager = TrackManager()
    mbid = "mock-mbid"

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{mbid}",
    ).mock(return_value=httpx.Response(200, json={"mbid": mbid, "name": "MbArtist"}))

    # Act
    result = await manager.get_mbartist(mbid)

    # Assert
    assert result["mbid"] == mbid
    assert result["name"] == "MbArtist"
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to get the MB artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_get_mbartist_not_found(respx_mock):
    # Arrange
    manager = TrackManager()
    mbid = "mock-mbid"

    respx_mock.route(
        method="GET",
        port=manager.api_port,
        host=manager.api_host,
        path=f"/api/mbartist/mbid/{mbid}",
    ).mock(return_value=httpx.Response(404))

    # Act
    result = await manager.get_mbartist(mbid)

    # Assert
    assert result is None
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to get the MB artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_post_mbartist_success(respx_mock):
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

    respx_mock.route(
        method="POST",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/mbartist",
    ).mock(
        return_value=httpx.Response(
            200, json={"id": 99, "name": "MbArtist", "aliases": []}
        )
    )

    # Act
    await manager.post_mbartist(artist)

    # Assert
    assert (
        respx_mock.calls.call_count == 1
    ), "Expected one call to post the MB artist, but found a different number."


@pytest.mark.asyncio
@respx.mock(assert_all_mocked=True)
async def test_post_mbartist_conflict(respx_mock):
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

    respx_mock.route(
        method="POST",
        port=manager.api_port,
        host=manager.api_host,
        path="/api/mbartist",
    ).mock(return_value=httpx.Response(409))

    # Act & Assert
    with pytest.raises(Exception) as excinfo:
        await manager.post_mbartist(artist)
    assert "Artist with MBID" in str(excinfo.value)
