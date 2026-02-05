"""API tests for listings endpoints."""


class TestListingsAPI:
    async def test_create_listing(self, client):
        response = await client.post("/api/v1/listings", json={
            "sku": "API-001",
            "title": "!!!AMAZING Nike Air Max 90 WOW!!!",
            "purchase_price": 20,
            "list_price": 50,
            "brand": "Nike",
            "model": "Air Max 90",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["sku"] == "API-001"
        assert "Nike" in data["title_sanitized"]
        assert "!!!" not in data["title_sanitized"]
        assert data["profit"]["meets_floor"] is True

    async def test_list_listings_empty(self, client):
        response = await client.get("/api/v1/listings")
        assert response.status_code == 200
        assert response.json() == []

    async def test_list_after_create(self, client):
        await client.post("/api/v1/listings", json={
            "sku": "API-002",
            "title": "Test Item",
            "purchase_price": 10,
            "list_price": 30,
        })
        response = await client.get("/api/v1/listings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["sku"] == "API-002"

    async def test_get_listing_by_id(self, client):
        create_resp = await client.post("/api/v1/listings", json={
            "sku": "API-003",
            "title": "Get Test",
            "purchase_price": 10,
            "list_price": 30,
        })
        listing_id = create_resp.json()["id"]

        response = await client.get(f"/api/v1/listings/{listing_id}")
        assert response.status_code == 200
        assert response.json()["sku"] == "API-003"

    async def test_get_nonexistent_listing(self, client):
        response = await client.get("/api/v1/listings/99999")
        assert response.status_code == 404

    async def test_create_low_profit_warning(self, client):
        response = await client.post("/api/v1/listings", json={
            "sku": "API-004",
            "title": "Low Profit Item",
            "purchase_price": 12,
            "list_price": 15,
            "shipping_cost": 3,
        })
        assert response.status_code == 201
        assert response.json()["profit"]["meets_floor"] is False
