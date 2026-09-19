import pytest


def company(client, name="Empresa Teste DRE"):
    response = client.post("/companies", json={"name": name, "segment": "Serviços"})
    assert response.status_code == 201
    return response.json()["data"]


def test_create_company(client):
    c = company(client)
    assert c["name"] == "Empresa Teste DRE"
    assert c["currency"] == "BRL" and c["guided_mode"] is True
    assert c["cnpj"] is None and c["created_at"] and c["updated_at"]


def test_list_company(client):
    assert client.get("/companies").json() == {"data": []}
    c = company(client)
    assert client.get("/companies").json()["data"] == [c]


def test_read_company(client):
    c = company(client)
    assert client.get(f"/companies/{c['id']}").json()["data"] == c


def test_patch_company(client):
    c = company(client)
    response = client.patch(
        f"/companies/{c['id']}",
        json={
            "name": "Nova empresa",
            "guided_mode": False,
            "cnpj": "123",
            "currency": "usd",
        },
    )
    assert response.status_code == 200
    updated = client.get(f"/companies/{c['id']}").json()["data"]
    assert updated["name"] == "Nova empresa" and updated["guided_mode"] is False
    assert updated["currency"] == "USD" and updated["segment"] == "Serviços"
    assert updated["updated_at"] >= c["updated_at"]
    assert (
        client.patch(f"/companies/{c['id']}", json={"cnpj": None}).json()["data"][
            "cnpj"
        ]
        is None
    )


@pytest.mark.parametrize("name", ["", "   ", None])
def test_empty_name(client, name):
    response = client.post("/companies", json={"name": name})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_missing_name(client):
    assert client.post("/companies", json={}).status_code == 422


@pytest.mark.parametrize(
    "patch",
    [
        {"name": ""},
        {"name": None},
        {"currency": None},
        {"guided_mode": None},
        {"status": "closed"},
    ],
)
def test_invalid_patch(client, patch):
    c = company(client)
    assert client.patch(f"/companies/{c['id']}", json=patch).status_code == 422
    assert client.get(f"/companies/{c['id']}").json()["data"]["name"] == c["name"]


def test_period_create_read_list(client):
    c = company(client)
    path = f"/companies/{c['id']}/periods"
    assert client.get(path).json() == {"data": []}
    response = client.post(path, json={"month": 8, "year": 2026})
    assert response.status_code == 201
    p = response.json()["data"]
    assert p["company_id"] == c["id"] and p["month"] == 8 and p["year"] == 2026
    assert p["status"] == "draft" and p["completion_percentage"] == 0
    assert p["closed_at"] is None and p["reopened_at"] is None
    assert client.get(f"/periods/{p['id']}").json()["data"] == p
    assert client.get(path).json()["data"] == [p]


@pytest.mark.parametrize("month", [0, 13, -1, 1.5, "8", True])
def test_invalid_month(client, month):
    c = company(client)
    assert (
        client.post(
            f"/companies/{c['id']}/periods", json={"month": month, "year": 2026}
        ).status_code
        == 422
    )


@pytest.mark.parametrize("year", [0, 1899, 2101, 2026.5, "2026", True])
def test_invalid_year(client, year):
    c = company(client)
    assert (
        client.post(
            f"/companies/{c['id']}/periods", json={"month": 8, "year": year}
        ).status_code
        == 422
    )


def test_unknown_company_period(client):
    r = client.post("/companies/999/periods", json={"month": 8, "year": 2026})
    assert r.status_code == 404 and r.json()["error"]["code"] == "COMPANY_NOT_FOUND"


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("get", "/companies/999", None),
        ("patch", "/companies/999", {"name": "Test"}),
        ("get", "/companies/999/periods", None),
        ("get", "/periods/999", None),
    ],
)
def test_not_found(client, method, path, body):
    response = client.request(method, path, json=body)
    assert response.status_code == 404 and "error" in response.json()


def test_duplicate_period(client):
    c = company(client)
    path = f"/companies/{c['id']}/periods"
    assert client.post(path, json={"month": 8, "year": 2026}).status_code == 201
    r = client.post(path, json={"month": 8, "year": 2026})
    assert r.status_code == 409
    assert r.json() == {
        "error": {
            "code": "PERIOD_ALREADY_EXISTS",
            "message": "Já existe um período de DRE para esta empresa neste mês e ano.",
            "details": {},
        }
    }
    assert len(client.get(path).json()["data"]) == 1


def test_same_month_different_companies(client):
    for name in ["A", "B"]:
        c = company(client, name)
        assert (
            client.post(
                f"/companies/{c['id']}/periods", json={"month": 8, "year": 2026}
            ).status_code
            == 201
        )


def test_forbid_period_status_input(client):
    c = company(client)
    assert (
        client.post(
            f"/companies/{c['id']}/periods",
            json={"month": 8, "year": 2026, "status": "closed"},
        ).status_code
        == 422
    )
