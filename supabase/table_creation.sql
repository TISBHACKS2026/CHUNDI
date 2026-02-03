CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

  user_id UUID NOT NULL
    REFERENCES auth.users(id)
    ON DELETE CASCADE,

  topic TEXT NOT NULL,

  content TEXT NOT NULL

);
CREATE INDEX documents_user_id_idx
ON documents (user_id);

CREATE INDEX documents_user_topic_idx
ON documents (user_id, topic);
ALTER TABLE documents
ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can access their own documents"
ON documents
FOR ALL
USING (user_id = (select auth.uid()))
WITH CHECK (user_id = (select auth.uid()));
