import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./tests_bootstrap.db")
os.environ.setdefault("JWT_SECRET_KEY", "x" * 32)
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-api-key")


import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from api.core.security import hash_password
from api.database import Base, get_db
from api.models import User


class DummyEmbeeddingGenerator:
    def embed_batch(self, texts):
        return [[0.0,0.0,0.0] for _ in texts]
    def embed_text(self, text):
        return [0.0,0.0,0.0]



class DummyRetriever:
    def retrieve_with_context(self, query, top_k=5,user_id=None):
        return {
            "query": query,
            "chunks": [],
            "context_text": "",
            num_results": 0,
        }

class DummyAnswerGenerator:
    def generate(self, query, context_text, source_files, message_history=None):
        from generation.answer_generator import GenerationResult

        return GenerationResult(
            answer="stub answer",
            source_used=source_files,
            refused=False
        )

@pytest.fixture()
def app(monkeypatch,tmp_path):
    import api.services.runtime_services as runtime_services

    monkeypatch.setattr(runtime_services, "get_embedding_generator",lambda: DummyEmbedddingGenerator())
    monkeypatch.setattr(runtime_services, "get_retriever",lambda: DummyRetriever())
    monkeypatch.setattr(runtime_services, "get_answer_generator",lambda: DummyAnswerGenerator())


    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}"),
    connect_args={"check_same_thread":False}

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    import api.main as main

    from api.rate_limiter import limiter

    limiter.enabled = False
    main.app.dependency_overrides[get_db] = override_get_db
    main.app.state.testing_session_factory = TestingSessionLocal

    yield main.app

    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()

@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield test_client

@pytest.fixture()
def db_session(app):
    SessionLocal = app.state.testing_session_factory
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def make_user(db_session):
    counter = {"value": 0}

    def _make_user(**overrides):
        counter["value"] += 1
        raw_password = overrides.pop("raw_password", "Password1!")
        user = User(
            email=overrides.pop("email",f"user{counter['value']}@example.com"),
            hashed_password=hash_password(raw_password),
            is_active=overrides.pop("is_active", True),
            is_verified=overrides.pop("is_verified", True),
            is_admin=overrides.pop("is_admin", False),
            auth_provider=overrides.pop("auth_provider", None),
            oauth_sub=overrides.pop("oauth_sub", None),
            plan_id=overrides.pop("plan_id", "free"),
            stripe_customer_id=overrides.pop("stripe_customer_id", None),
            stripe_subscription_id=overrides.pop("stripe_subscription_id", None),
            billing_status=overrides.pop("billing_status", None),
        )

        for key, value in overrides.items():
            setattr(user,key,value)

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        user._raw_password = raw_password
        return user

    return _make_user

@pytest.fixture()
def force_current_user(app):
    from api.dependencies import get_current_user
    
    def _force(user):
        app.dependency_overrides[get_current_user] = lambda: user
        return user

    yeild _force

    app.dependency_overrides.pop(get_current_user,None)