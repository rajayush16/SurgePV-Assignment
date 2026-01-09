from app.crud.users import create_user


def test_create_and_list_issues(client, db_session):
    assignee = create_user(db_session, "Alex", "alex@example.com")
    db_session.commit()

    response = client.post(
        "/issues",
        json={"title": "Login bug", "description": "Fails on retry", "assignee_id": assignee.id},
    )
    assert response.status_code == 201
    issue_id = response.json()["id"]

    label_response = client.put(f"/issues/{issue_id}/labels", json={"labels": ["bug", "urgent"]})
    assert label_response.status_code == 200

    list_response = client.get("/issues", params={"assignee_id": assignee.id})
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == issue_id

    label_filter = client.get("/issues", params={"label": "urgent"})
    assert label_filter.status_code == 200
    assert label_filter.json()["total"] == 1
