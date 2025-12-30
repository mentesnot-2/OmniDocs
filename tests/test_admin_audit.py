from api.models import AdminAuditLog


def test_admin_action_writes_audit_log(client, db_session, make_user, force_current_user):
    admin = make_user(is_admin=True, email="admin@example.com")
    target = make_user(email="target@example.com")
    force_current_user(admin)

    response = client.patch(
        f"/admin/users/{target.id}/active",
        json={"is_active": False},
    )
    assert response.status_code == 200

    logs = db_session.query(AdminAuditLog).all()
    assert len(logs) == 1
    assert logs[0].action == "user.set_active"
    assert logs[0].target_id == str(target.id)

    audit_api = client.get("/admin/audit-logs")
    assert audit_api.status_code == 200
    assert len(audit_api.json()["logs"]) >= 1
