from app.crud.users import create_user


def test_bulk_status_rolls_back(client, db_session):
    assignee = create_user(db_session, "Sam", "sam@example.com")
    db_session.commit()

    issue_one = client.post("/issues", json={"title": "One", "assignee_id": assignee.id}).json()
    issue_two = client.post("/issues", json={"title": "Two"}).json()

    response = client.post(
        "/issues/bulk-status",
        json={"issue_ids": [issue_one["id"], issue_two["id"]], "new_status": "RESOLVED"},
    )
    assert response.status_code == 400

    issue_one_after = client.get(f"/issues/{issue_one['id']}").json()
    issue_two_after = client.get(f"/issues/{issue_two['id']}").json()
    assert issue_one_after["status"] == "OPEN"
    assert issue_two_after["status"] == "OPEN"
