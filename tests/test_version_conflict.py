from app.crud.users import create_user


def test_version_conflict(client, db_session):
    assignee = create_user(db_session, "Priya", "priya@example.com")
    db_session.commit()

    response = client.post("/issues", json={"title": "Race condition", "assignee_id": assignee.id})
    assert response.status_code == 201
    issue = response.json()

    conflict = client.patch(
        f"/issues/{issue['id']}",
        json={"title": "Updated title", "version": issue["version"] + 1},
    )
    assert conflict.status_code == 409

    fetched = client.get(f"/issues/{issue['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Race condition"
