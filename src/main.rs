mod notebook;

use gio::prelude::*;
use glib::clone;
use gtk::prelude::*;
use gtk::{
    AboutDialog, AccelFlags, AccelGroup, ApplicationWindow, CheckMenuItem, IconSize, Image, Label,
    Menu, MenuBar, MenuItem, WindowPosition, SeparatorMenuItem
};
use std::env::args;
use notebook::*;


fn build_ui(application: &gtk::Application) {
    
    let window = ApplicationWindow::new(application);

    window.set_title("RegView");
    window.set_position(WindowPosition::Center);
    window.set_size_request(400, 400);

    let v_box = gtk::Box::new(gtk::Orientation::Vertical, 10);

    let menu = Menu::new();
    let accel_group = AccelGroup::new();
    window.add_accel_group(&accel_group);

    let menu_bar = MenuBar::new();
    let file = MenuItem::with_label("File");
    let open = MenuItem::with_label("Open");
    let quit = MenuItem::with_label("Quit");

    menu.append(&open);
    menu.append(&SeparatorMenuItem::new());
    menu.append(&quit);

    file.set_submenu(Some(&menu));
    menu_bar.append(&file);

    quit.connect_activate(clone!(@weak window => move |_| {
        window.close();
    }));

    // `Primary` is `Ctrl` on Windows and Linux, and `command` on macOS
    // It isn't available directly through gdk::ModifierType, since it has
    // different values on different platforms.
    let (key, modifier) = gtk::accelerator_parse("<Primary>Q");
    quit.add_accelerator("activate", &accel_group, key, modifier, AccelFlags::VISIBLE);

    v_box.pack_start(&menu_bar, false, false, 0);
    window.add(&v_box);

    let mut notebook = Notebook::new();

    for i in 1..4 {
        let title = format!("sheet {}", i);
        let label = gtk::Label::new(Some(&*title));
        notebook.create_tab(&title, label.upcast());
    }

    v_box.pack_start(notebook.notebook(), true, true, 0);
    window.show_all();
}

fn main() {
    let application = gtk::Application::new(
        Some("com.github.gtk-rs.examples.menu_bar"),
        Default::default(),
    )
    .expect("Initialization failed...");

    application.connect_activate(|app| {
        build_ui(app);
    });

    application.run(&args().collect::<Vec<_>>());
}
