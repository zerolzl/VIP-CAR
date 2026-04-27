import pytest
import json

class TestSpotsAPI:
    def test_create_spot(self, client):
        response = client.post("/api/spots", json={
            "spot_number": "A01",
            "owner": "张三",
            "allowed_plates": ["粤B12345", "粤B67890"],
            "status": 1
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["spot_number"] == "A01"

    def test_get_spots(self, client):
        # 先创建
        client.post("/api/spots", json={
            "spot_number": "A02",
            "owner": "李四",
            "allowed_plates": ["粤B11111"],
            "status": 1
        })
        response = client.get("/api/spots")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["total"] >= 1

    def test_update_spot(self, client):
        # 先创建
        create_resp = client.post("/api/spots", json={
            "spot_number": "A03",
            "owner": "王五",
            "allowed_plates": ["粤B22222"],
            "status": 1
        })
        spot_id = create_resp.json()["data"]["id"]
        # 更新
        response = client.put(f"/api/spots/{spot_id}", json={
            "owner": "王五更新"
        })
        assert response.status_code == 200

    def test_delete_spot(self, client):
        create_resp = client.post("/api/spots", json={
            "spot_number": "A04",
            "owner": "赵六",
            "allowed_plates": ["粤B33333"],
            "status": 1
        })
        spot_id = create_resp.json()["data"]["id"]
        response = client.delete(f"/api/spots/{spot_id}")
        assert response.status_code == 200

    def test_duplicate_spot_number(self, client):
        client.post("/api/spots", json={
            "spot_number": "A05",
            "owner": "测试",
            "allowed_plates": ["粤B44444"],
            "status": 1
        })
        # 重复车位编号应失败（IntegrityError被全局异常处理器捕获返回500）
        with pytest.raises(Exception):
            client.post("/api/spots", json={
                "spot_number": "A05",
                "owner": "重复",
                "allowed_plates": ["粤B55555"],
                "status": 1
            })
