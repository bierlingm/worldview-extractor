use std::fs;
use std::path::PathBuf;

use crate::models::Worldview;
use super::error::StorageError;

pub fn get_store_dir() -> PathBuf {
    let home = dirs::home_dir().expect("Could not find home directory");
    let store_dir = home.join(".wve").join("store");
    if !store_dir.exists() {
        fs::create_dir_all(&store_dir).expect("Failed to create store directory");
    }
    store_dir
}

pub fn get_worldview_dir(slug: &str) -> PathBuf {
    get_store_dir().join(slug)
}

pub fn save_worldview(worldview: &Worldview) -> Result<PathBuf, StorageError> {
    let dir = get_worldview_dir(&worldview.slug);
    fs::create_dir_all(&dir)?;

    let file_path = dir.join("worldview.json");
    let json = serde_json::to_string_pretty(worldview)?;
    fs::write(&file_path, json)?;

    Ok(file_path)
}

pub fn load_worldview(slug: &str) -> Result<Worldview, StorageError> {
    let file_path = get_worldview_dir(slug).join("worldview.json");

    if !file_path.exists() {
        return Err(StorageError::NotFound(slug.to_string()));
    }

    let json = fs::read_to_string(&file_path)?;
    let worldview: Worldview = serde_json::from_str(&json)?;

    Ok(worldview)
}

pub fn list_worldview_slugs() -> Result<Vec<String>, StorageError> {
    let store_dir = get_store_dir();
    let mut slugs = Vec::new();

    for entry in fs::read_dir(&store_dir)? {
        let entry = entry?;
        if entry.file_type()?.is_dir() {
            if let Some(name) = entry.file_name().to_str() {
                let worldview_file = entry.path().join("worldview.json");
                if worldview_file.exists() {
                    slugs.push(name.to_string());
                }
            }
        }
    }

    Ok(slugs)
}

pub fn delete_worldview(slug: &str) -> Result<(), StorageError> {
    let dir = get_worldview_dir(slug);

    if !dir.exists() {
        return Err(StorageError::NotFound(slug.to_string()));
    }

    fs::remove_dir_all(&dir)?;

    Ok(())
}
