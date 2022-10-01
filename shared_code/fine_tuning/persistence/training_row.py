from sqlalchemy import Column, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TrainingDataRow(Base):
	__tablename__ = "training"
	Subreddit = Column(Text)
	SubmissionId = Column(Text)
	SubmissionTitle = Column(Text)
	SubmissionAuthor = Column(Text)
	SubmissionContent = Column(Text)
	ParentId = Column(Text)
	ParentAuthor = Column(Text)
	ParentBody = Column(Text)
	GrandParentAuthor = Column(Text)
	CommentId = Column(Text, primary_key=True)
	CommentBody = Column(Text)
	CommentAuthor = Column(Text)
	TrainingString = Column(Text)