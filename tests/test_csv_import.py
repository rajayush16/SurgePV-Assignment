from app.crud.users import create_user


def test_csv_import_invalid_row(client, db_session):
    create_user(db_session, "Mia", "mia@example.com")
    db_session.commit()

    csv_data = "title,description,status,assignee_email,labels\n" "Bug,,OPEN,missing@example.com,bug\n"
    response = client.post(
        "/issues/import",
        files={"file": ("issues.csv", csv_data, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["created"] == 0
    assert payload["failed"] == 1

    listing = client.get("/issues").json()
    assert listing["total"] == 0


def test_csv_import_valid_file(client, db_session):
    create_user(db_session, "Noah", "noah@example.com")
    db_session.commit()

    csv_data = (
        "title,description,status,assignee_email,labels\n"
        "First issue,Desc,,noah@example.com,bug;urgent\n"
        "Second issue,Desc,IN_PROGRESS,noah@example.com,backend\n"
    )
    response = client.post(
        "/issues/import",
        files={"file": ("issues.csv", csv_data, "text/csv")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["created"] == 2
    assert payload["failed"] == 0
