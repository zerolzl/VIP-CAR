import pytest

class TestContactsAPI:
    def test_create_contact(self, client):
        response = client.post("/api/contacts", json={
            "name": "张三",
            "phone": "13800138000",
            "enabled": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "张三"

    def test_get_contacts(self, client):
        response = client.get("/api/contacts")
        assert response.status_code == 200
        assert response.json()["code"] == 200

    def test_update_contact(self, client):
        create_resp = client.post("/api/contacts", json={
            "name": "李四",
            "phone": "13900139000",
            "enabled": 1
        })
        contact_id = create_resp.json()["data"]["id"]
        response = client.put(f"/api/contacts/{contact_id}", json={"name": "李四更新"})
        assert response.status_code == 200

    def test_delete_contact(self, client):
        create_resp = client.post("/api/contacts", json={
            "name": "王五",
            "phone": "13700137000",
            "enabled": 1
        })
        contact_id = create_resp.json()["data"]["id"]
        response = client.delete(f"/api/contacts/{contact_id}")
        assert response.status_code == 200
