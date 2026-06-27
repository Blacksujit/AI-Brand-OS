from __future__ import annotations

import uuid

from services.history import HistoryService


class TestHistoryService:
    def setup_method(self) -> None:
        self.user_id = uuid.uuid4()
        self.other_user_id = uuid.uuid4()
        self.service = HistoryService()

    def test_record_generation(self) -> None:
        record = self.service.record_generation(
            user_id=self.user_id,
            title="Test Post",
            body="This is a test post body.",
            platform="linkedin",
        )
        assert record.id is not None
        assert record.title == "Test Post"
        assert record.body == "This is a test post body."
        assert record.platform == "linkedin"
        assert record.status == "draft"
        assert record.quality_score is None
        assert record.tokens_used == 0

    def test_record_with_full_data(self) -> None:
        record = self.service.record_generation(
            user_id=self.user_id,
            title="AI Trends",
            body="AI is changing everything.",
            platform="twitter",
            quality_score=0.92,
            review_feedback="Great post",
            hook="Did you know?",
            call_to_action="Share your thoughts",
            hashtags=["#AI", "#Tech"],
            tokens_used=150,
            llm_model="gemini-pro",
            duration_ms=1200,
        )
        assert record.quality_score == 0.92
        assert record.review_feedback == "Great post"
        assert record.hook == "Did you know?"
        assert record.call_to_action == "Share your thoughts"
        assert record.hashtags == ["#AI", "#Tech"]
        assert record.tokens_used == 150
        assert record.llm_model == "gemini-pro"
        assert record.duration_ms == 1200

    def test_get_history(self) -> None:
        self.service.record_generation(user_id=self.user_id, title="Post 1", body="Body 1")
        self.service.record_generation(user_id=self.user_id, title="Post 2", body="Body 2")
        self.service.record_generation(
            user_id=self.other_user_id, title="Other Post", body="Other Body"
        )
        history = self.service.get_history(user_id=self.user_id)
        assert len(history) == 2
        assert history[0].title == "Post 2"

    def test_get_history_with_filters(self) -> None:
        self.service.record_generation(
            user_id=self.user_id,
            title="LinkedIn Post",
            body="Body",
            platform="linkedin",
        )
        self.service.record_generation(
            user_id=self.user_id,
            title="Twitter Post",
            body="Body",
            platform="twitter",
        )
        linkedin_only = self.service.get_history(user_id=self.user_id, platform="linkedin")
        assert len(linkedin_only) == 1
        assert linkedin_only[0].platform == "linkedin"

    def test_get_history_limit_and_offset(self) -> None:
        for i in range(10):
            self.service.record_generation(
                user_id=self.user_id, title=f"Post {i}", body=f"Body {i}"
            )
        first_page = self.service.get_history(user_id=self.user_id, limit=3, offset=0)
        assert len(first_page) == 3
        second_page = self.service.get_history(user_id=self.user_id, limit=3, offset=3)
        assert len(second_page) == 3
        assert first_page[0].title != second_page[0].title

    def test_get_record(self) -> None:
        created = self.service.record_generation(user_id=self.user_id, title="Find Me", body="Body")
        found = self.service.get_record(user_id=self.user_id, record_id=created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_record_wrong_user(self) -> None:
        created = self.service.record_generation(user_id=self.user_id, title="Mine", body="Body")
        found = self.service.get_record(user_id=self.other_user_id, record_id=created.id)
        assert found is None

    def test_get_record_not_found(self) -> None:
        found = self.service.get_record(user_id=self.user_id, record_id=uuid.uuid4())
        assert found is None

    def test_update_status(self) -> None:
        created = self.service.record_generation(
            user_id=self.user_id, title="To Publish", body="Body"
        )
        updated = self.service.update_status(
            user_id=self.user_id,
            record_id=created.id,
            status="published",
        )
        assert updated is not None
        assert updated.status == "published"

    def test_update_status_nonexistent(self) -> None:
        updated = self.service.update_status(
            user_id=self.user_id,
            record_id=uuid.uuid4(),
            status="published",
        )
        assert updated is None

    def test_update_status_wrong_user(self) -> None:
        created = self.service.record_generation(user_id=self.user_id, title="Mine", body="Body")
        updated = self.service.update_status(
            user_id=self.other_user_id,
            record_id=created.id,
            status="published",
        )
        assert updated is None

    def test_wire_repo(self) -> None:
        fake_repo = object()
        self.service.wire(fake_repo)
        assert self.service._repo is fake_repo

    def test_multiple_users_isolation(self) -> None:
        u1 = uuid.uuid4()
        u2 = uuid.uuid4()
        for i in range(5):
            self.service.record_generation(user_id=u1, title=f"U1 Post {i}", body="Body")
            self.service.record_generation(user_id=u2, title=f"U2 Post {i}", body="Body")
        assert len(self.service.get_history(user_id=u1)) == 5
        assert len(self.service.get_history(user_id=u2)) == 5
