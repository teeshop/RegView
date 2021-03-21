use gio::prelude::*;
use glib::clone;
use gtk::prelude::*;
use gtk::{IconSize, Orientation, ReliefStyle, Widget};

pub struct Notebook {
    notebook: gtk::Notebook,
    tabs: Vec<gtk::Box>,
}

impl Notebook {
    pub fn new() -> Notebook {
        Notebook {
            notebook: gtk::Notebook::new(),
            tabs: Vec::new(),
        }
    }

    pub fn create_tab(&mut self, title: &str, widget: Widget) -> u32 {
        let close_image = gtk::Image::from_icon_name(Some("window-close"), IconSize::Button);
        let button = gtk::Button::new();
        let label = gtk::Label::new(Some(title));
        let tab = gtk::Box::new(Orientation::Horizontal, 0);

        button.set_relief(ReliefStyle::None);
        button.set_focus_on_click(false);
        button.add(&close_image);

        tab.pack_start(&label, false, false, 0);
        tab.pack_start(&button, false, false, 0);
        tab.show_all();

        let index = self.notebook.append_page(&widget, Some(&tab));

        button.connect_clicked(clone!(@weak self.notebook as notebook => move |_| {
            let index = notebook
                .page_num(&widget)
                .expect("Couldn't get page_num from notebook");
            notebook.remove_page(Some(index));
        }));

        self.tabs.push(tab);

        index
    }
    pub fn notebook(&self) -> &gtk::Notebook {
        &self.notebook
    }
}