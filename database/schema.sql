-- PsiTerm v0.2.0 PostgreSQL schema draft.
-- Backend must enforce authorization and protected-path rules; frontend checks are not security controls.
CREATE TABLE IF NOT EXISTS users (
 id BIGSERIAL PRIMARY KEY, username VARCHAR(64) NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 role VARCHAR(16) NOT NULL DEFAULT 'simple' CHECK(role IN ('simple','expert','admin')),
 is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS devices (
 id BIGSERIAL PRIMARY KEY, cpid VARCHAR(64) NOT NULL UNIQUE, name VARCHAR(128) NOT NULL,
 ip_address INET NOT NULL, ssh_port INTEGER NOT NULL DEFAULT 22 CHECK(ssh_port BETWEEN 1 AND 65535),
 ssh_username VARCHAR(64), description TEXT, is_active BOOLEAN NOT NULL DEFAULT TRUE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS user_device_access (
 user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 device_id BIGINT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
 can_connect BOOLEAN NOT NULL DEFAULT FALSE, can_download BOOLEAN NOT NULL DEFAULT FALSE,
 can_upload BOOLEAN NOT NULL DEFAULT FALSE, PRIMARY KEY(user_id,device_id)
);
CREATE TABLE IF NOT EXISTS user_preferences (
 user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 language VARCHAR(2) NOT NULL DEFAULT 'ru' CHECK(language IN ('ru','kk','en')),
 theme VARCHAR(8) NOT NULL DEFAULT 'light' CHECK(theme IN ('light','dark')),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS user_favorite_devices (
 user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 device_id BIGINT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), PRIMARY KEY(user_id,device_id)
);
CREATE TABLE IF NOT EXISTS device_comments (
 id BIGSERIAL PRIMARY KEY, device_id BIGINT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
 author_user_id BIGINT NOT NULL REFERENCES users(id), body TEXT NOT NULL DEFAULT '',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS comment_attachments (
 id BIGSERIAL PRIMARY KEY, comment_id BIGINT NOT NULL REFERENCES device_comments(id) ON DELETE CASCADE,
 storage_key TEXT NOT NULL, original_name TEXT NOT NULL, mime_type VARCHAR(127) NOT NULL,
 size_bytes BIGINT NOT NULL CHECK(size_bytes BETWEEN 1 AND 52428800)
);
CREATE TABLE IF NOT EXISTS service_tickets (
 id BIGSERIAL PRIMARY KEY, device_id BIGINT REFERENCES devices(id) ON DELETE SET NULL,
 created_by BIGINT NOT NULL REFERENCES users(id), category VARCHAR(64) NOT NULL,
 description TEXT NOT NULL, status VARCHAR(24) NOT NULL DEFAULT 'new',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS protected_paths (
 id BIGSERIAL PRIMARY KEY, device_id BIGINT REFERENCES devices(id) ON DELETE CASCADE,
 path TEXT NOT NULL, can_download BOOLEAN NOT NULL DEFAULT FALSE,
 can_modify BOOLEAN NOT NULL DEFAULT FALSE, UNIQUE(device_id,path)
);
-- Seed examples of protected system paths per device in backend migrations:
-- /home, /home/psi2, /home/psiuser, /etc, /var
CREATE TABLE IF NOT EXISTS audit_log (
 id BIGSERIAL PRIMARY KEY, actor_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
 device_id BIGINT REFERENCES devices(id) ON DELETE SET NULL, action VARCHAR(64) NOT NULL,
 details JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_devices_active ON devices(is_active);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tickets_created_at ON service_tickets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_device_comments_device_date ON device_comments(device_id,created_at);
