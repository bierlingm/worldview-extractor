use rusqlite::{Connection, params};
use std::path::PathBuf;

use super::error::StorageError;

#[derive(Debug, Clone)]
pub struct WorldviewMeta {
    pub id: i64,
    pub slug: String,
    pub subject: String,
    pub created_at: String,
    pub updated_at: String,
    pub point_count: i64,
    pub source_count: i64,
}

fn get_db_path() -> PathBuf {
    let home = dirs::home_dir().expect("Could not find home directory");
    home.join(".wve").join("index.sqlite")
}

pub fn init_db() -> Result<Connection, StorageError> {
    let db_path = get_db_path();
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent)?;
    }

    let conn = Connection::open(&db_path)?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS worldviews (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            point_count INTEGER NOT NULL,
            source_count INTEGER NOT NULL
        )",
        [],
    )?;

    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS worldviews_fts USING fts5(
            slug,
            subject,
            themes
        )",
        [],
    )?;

    Ok(conn)
}

pub fn insert_worldview_index(conn: &Connection, meta: &WorldviewMeta, themes: &str) -> Result<(), StorageError> {
    conn.execute(
        "INSERT OR REPLACE INTO worldviews (id, slug, subject, created_at, updated_at, point_count, source_count)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        params![
            meta.id,
            meta.slug,
            meta.subject,
            meta.created_at,
            meta.updated_at,
            meta.point_count,
            meta.source_count,
        ],
    )?;

    conn.execute(
        "DELETE FROM worldviews_fts WHERE slug = ?1",
        params![meta.slug],
    )?;

    conn.execute(
        "INSERT INTO worldviews_fts (slug, subject, themes) VALUES (?1, ?2, ?3)",
        params![meta.slug, meta.subject, themes],
    )?;

    Ok(())
}

pub fn get_worldview_meta(conn: &Connection, slug: &str) -> Result<WorldviewMeta, StorageError> {
    let mut stmt = conn.prepare(
        "SELECT id, slug, subject, created_at, updated_at, point_count, source_count
         FROM worldviews WHERE slug = ?1",
    )?;

    let meta = stmt.query_row(params![slug], |row| {
        Ok(WorldviewMeta {
            id: row.get(0)?,
            slug: row.get(1)?,
            subject: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
            point_count: row.get(5)?,
            source_count: row.get(6)?,
        })
    }).map_err(|e| match e {
        rusqlite::Error::QueryReturnedNoRows => StorageError::NotFound(slug.to_string()),
        _ => StorageError::Sqlite(e),
    })?;

    Ok(meta)
}

pub fn list_worldviews(conn: &Connection) -> Result<Vec<WorldviewMeta>, StorageError> {
    let mut stmt = conn.prepare(
        "SELECT id, slug, subject, created_at, updated_at, point_count, source_count
         FROM worldviews ORDER BY updated_at DESC",
    )?;

    let iter = stmt.query_map([], |row| {
        Ok(WorldviewMeta {
            id: row.get(0)?,
            slug: row.get(1)?,
            subject: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
            point_count: row.get(5)?,
            source_count: row.get(6)?,
        })
    })?;

    let mut results = Vec::new();
    for meta in iter {
        results.push(meta?);
    }

    Ok(results)
}

pub fn search_worldviews(conn: &Connection, query: &str) -> Result<Vec<WorldviewMeta>, StorageError> {
    let mut stmt = conn.prepare(
        "SELECT w.id, w.slug, w.subject, w.created_at, w.updated_at, w.point_count, w.source_count
         FROM worldviews w
         JOIN worldviews_fts fts ON w.slug = fts.slug
         WHERE worldviews_fts MATCH ?1
         ORDER BY rank",
    )?;

    let iter = stmt.query_map(params![query], |row| {
        Ok(WorldviewMeta {
            id: row.get(0)?,
            slug: row.get(1)?,
            subject: row.get(2)?,
            created_at: row.get(3)?,
            updated_at: row.get(4)?,
            point_count: row.get(5)?,
            source_count: row.get(6)?,
        })
    })?;

    let mut results = Vec::new();
    for meta in iter {
        results.push(meta?);
    }

    Ok(results)
}
