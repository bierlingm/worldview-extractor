use bubbles::list::{DefaultDelegate, Item, List};
use bubbles::viewport::Viewport;
use bubbletea::{Cmd, KeyMsg, KeyType, Message, Model, Program};
use lipgloss::Style;

use crate::models::Worldview;
use crate::storage::json_store;

pub enum Screen {
    Home,
    WorldviewList,
    WorldviewDetail(String),
}

#[derive(Clone)]
pub struct WorldviewListItem {
    pub slug: String,
    pub subject: String,
    pub date: String,
}

impl Item for WorldviewListItem {
    fn filter_value(&self) -> &str {
        &self.subject
    }
}

pub struct App {
    screen: Screen,
    width: u16,
    height: u16,
    worldview_list: List<WorldviewListItem, DefaultDelegate>,
    detail_viewport: Viewport,
    worldviews: Vec<(String, String, String)>,
    selected_worldview: Option<Worldview>,
}

impl App {
    pub fn new() -> Self {
        let worldviews = load_worldview_list();
        let items: Vec<WorldviewListItem> = worldviews
            .iter()
            .map(|(slug, subject, date)| WorldviewListItem {
                slug: slug.clone(),
                subject: subject.clone(),
                date: date.clone(),
            })
            .collect();

        let delegate = DefaultDelegate::new().with_height(2).with_spacing(1);
        let list = List::new(items, delegate, 80, 20).title("Stored Worldviews");

        Self {
            screen: Screen::Home,
            width: 80,
            height: 24,
            worldview_list: list,
            detail_viewport: Viewport::new(80, 20),
            worldviews,
            selected_worldview: None,
        }
    }
}

impl Model for App {
    fn init(&self) -> Option<Cmd> {
        None
    }

    fn update(&mut self, msg: Message) -> Option<Cmd> {
        if let Some(key) = msg.downcast_ref::<KeyMsg>() {
            match key.key_type {
                KeyType::CtrlC => return Some(bubbletea::quit()),
                KeyType::Runes if key.runes == vec!['q'] => return Some(bubbletea::quit()),
                KeyType::Runes if key.runes == vec!['l'] || key.runes == vec!['L'] => {
                    if matches!(self.screen, Screen::Home) {
                        self.screen = Screen::WorldviewList;
                        return None;
                    }
                }
                KeyType::Enter => {
                    if matches!(self.screen, Screen::WorldviewList) {
                        if let Some(item) = self.worldview_list.selected_item() {
                            let slug = item.slug.clone();
                            if let Ok(wv) = json_store::load_worldview(&slug) {
                                let content = format_worldview_detail(&wv);
                                self.detail_viewport.set_content(&content);
                                self.selected_worldview = Some(wv);
                                self.screen = Screen::WorldviewDetail(slug);
                            }
                        }
                        return None;
                    }
                }
                KeyType::Esc => {
                    match &self.screen {
                        Screen::WorldviewDetail(_) => self.screen = Screen::WorldviewList,
                        Screen::WorldviewList => self.screen = Screen::Home,
                        Screen::Home => return Some(bubbletea::quit()),
                    }
                    return None;
                }
                _ => {}
            }
        }

        match &self.screen {
            Screen::WorldviewList => {
                self.worldview_list.update(msg);
            }
            Screen::WorldviewDetail(_) => {
                self.detail_viewport.update(&msg);
            }
            _ => {}
        }

        None
    }

    fn view(&self) -> String {
        let title_style = Style::new().bold().foreground("#7c3aed");
        let hint_style = Style::new().faint();

        match &self.screen {
            Screen::Home => {
                let mut output = String::new();
                output.push_str(&title_style.render("wve - worldview extractor"));
                output.push_str("\n\n");
                output.push_str(&format!("{} worldviews stored\n\n", self.worldviews.len()));
                output.push_str(&hint_style.render("l: list worldviews | n: new extraction | q: quit"));
                output
            }
            Screen::WorldviewList => {
                let mut output = String::new();
                output.push_str(&title_style.render("Stored Worldviews"));
                output.push_str("\n\n");
                output.push_str(&self.worldview_list.view());
                output.push_str("\n\n");
                output.push_str(&hint_style.render("↑/↓: navigate | enter: view | esc: back | q: quit"));
                output
            }
            Screen::WorldviewDetail(slug) => {
                let mut output = String::new();
                output.push_str(&title_style.render(&format!("Worldview: {}", slug)));
                output.push_str("\n\n");
                output.push_str(&self.detail_viewport.view());
                output.push_str("\n\n");
                output.push_str(&hint_style.render("↑/↓: scroll | esc: back | q: quit"));
                output
            }
        }
    }
}

fn load_worldview_list() -> Vec<(String, String, String)> {
    json_store::list_worldview_slugs()
        .unwrap_or_default()
        .into_iter()
        .filter_map(|slug| {
            json_store::load_worldview(&slug).ok().map(|wv| {
                (slug, wv.subject, wv.created_at.format("%Y-%m-%d").to_string())
            })
        })
        .collect()
}

fn format_worldview_detail(wv: &Worldview) -> String {
    let mut out = String::new();
    out.push_str(&format!("Subject: {}\n", wv.subject));
    out.push_str(&format!("Points: {}\n\n", wv.points.len()));

    for (i, point) in wv.points.iter().enumerate() {
        out.push_str(&format!(
            "{}. {} ({:.0}%)\n",
            i + 1,
            point.theme,
            point.confidence * 100.0
        ));
        out.push_str(&format!("   {}\n\n", point.stance));
    }
    out
}

pub fn run() -> anyhow::Result<()> {
    let app = App::new();
    Program::new(app).with_alt_screen().run()?;
    Ok(())
}
