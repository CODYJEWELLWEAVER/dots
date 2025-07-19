from typing import Callable
from fabric.widgets.box import Box
from fabric.widgets.centerbox import CenterBox
from fabric.widgets.label import Label
from fabric.widgets.button import Button
from fabric.widgets.scrolledwindow import ScrolledWindow
from fabric.widgets.entry import Entry

from services.todo import ToDoService, ToDoItemParent, ToDoItem
from util.ui import add_hover_cursor, toggle_visible
import config.icons as Icons


class ToDoListElement(Box):
    def __init__(
        self,
        item: ToDoItem,
        on_toggle_completed: Callable,
        on_delete: Callable,
        on_add_child: Callable = lambda *_: None,
        **kwargs,
    ):
        is_child_element = not isinstance(item, ToDoItemParent)

        super().__init__(
            spacing=20, orientation="h", style_classes="to-do-item", **kwargs
        )

        if is_child_element:
            self.add_style_class("to-do-item-child")

        checkbox_label = Label(
            style_classes="to-do-item-icon",
            markup=Icons.checkbox_checked
            if item.completed
            else Icons.checkbox_unchecked,
        )
        checkbox = Button(
            style_classes="checkbox-button",
            child=checkbox_label,
            on_clicked=on_toggle_completed,
        )
        add_hover_cursor(checkbox)

        item_label = Label(
            style_classes="to-do-item-label",
            label=item.text,
            line_wrap="word-char",
            h_expand=True,
            h_align="start",
        )

        if not is_child_element:
            add_child_button = Button(
                child=Label(style_classes="to-do-item-icon", markup=Icons.hierarchy),
                on_clicked=on_add_child,
            )
            add_hover_cursor(add_child_button)

        delete_button = Button(
            child=Label(
                style_classes="to-do-item-icon",
                markup=Icons.delete,
            ),
            on_clicked=on_delete,
        )
        add_hover_cursor(delete_button)

        self.add(checkbox)
        self.add(item_label)
        if not is_child_element:
            self.add(add_child_button)
        self.add(delete_button)


class ToDoList(Box):
    def __init__(self, on_switch: Callable, **kwargs):
        super().__init__(
            name="to-do-list", spacing=10, orientation="v", v_expand=True, **kwargs
        )

        self.parent_item: ToDoItemParent | None = None

        self.to_do_service = ToDoService.get_instance()

        self.to_do_text_entry = Entry(
            name="to-do-text-entry", placeholder="text", h_expand=True, h_align="center"
        )

        self.add_button = Button(
            style_classes="add-to-do-button",
            h_expand=True,
            child=Label(
                label="Add",
            ),
            on_clicked=self.on_add_to_do,
        )
        add_hover_cursor(self.add_button)
        self.add_button.set_sensitive(False)

        self.cancel_add_button = Button(
            style_classes="add-to-do-button",
            h_expand=True,
            child=Label(
                label="Cancel",
            ),
            on_clicked=self.on_cancel_add_to_do,
        )
        add_hover_cursor(self.cancel_add_button)

        self.create_to_do_view = Box(
            name="create-to-do-view",
            spacing=20,
            h_expand=True,
            h_align="center",
            orientation="v",
            visible=False,
            children=[
                Label("Create To Do Item:"),
                self.to_do_text_entry,
                Box(
                    spacing=10,
                    orientation="h",
                    children=[self.add_button, self.cancel_add_button],
                ),
            ],
        )

        self.to_do_list = Box(
            name="to-do-list-box",
            orientation="v",
            spacing=10,
            h_expand=True,
            v_expand=True,
            children=self.get_to_do_list_elements(),
        )
        self.to_do_view = ScrolledWindow(
            name="to-do-view",
            h_expand=True,
            v_expand=True,
            child=self.to_do_list,
        )

        self.switch_button = Button(
            style_classes="productivity-switch-button",
            child=Label(
                label="To Do",
            ),
            on_clicked=on_switch,
        )
        add_hover_cursor(self.switch_button)

        self.create_button = Button(
            name="create-to-do-button",
            child=Label(
                markup=Icons.plus,
                name="create-to-do-label",
            ),
            on_clicked=self.show_creation_view,
        )
        add_hover_cursor(self.create_button)

        self.children = [
            CenterBox(
                v_align="center",
                center_children=self.switch_button,
                end_children=self.create_button,
            ),
            self.to_do_view,
            self.create_to_do_view,
        ]

        self.to_do_service.connect("changed", self.on_changed)

        self.to_do_text_entry.connect("notify::text", self.on_notify_text)

    def show_creation_view(self, *args, parent: ToDoItemParent | None = None):
        self.parent_item = parent
        self.toggle_view()

    def toggle_view(self, *args):
        toggle_visible(self.to_do_view)
        toggle_visible(self.create_to_do_view)
        self.create_button.set_sensitive(not self.create_to_do_view.is_visible())

    def get_to_do_list_elements(self):
        elements = []
        for item in self.to_do_service.to_do_list:
            elements.append(
                ToDoListElement(
                    item,
                    on_toggle_completed=lambda *_,
                    item=item: self.to_do_service.toggle_item_completed(item),
                    on_delete=lambda *_,
                    item=item: self.to_do_service.delete_to_do_item(item),
                    on_add_child=lambda *_, item=item: self.show_creation_view(
                        parent=item
                    ),
                )
            )
            for child in item.children.values():
                elements.append(
                    ToDoListElement(
                        child,
                        on_toggle_completed=lambda *_,
                        item=item,
                        child=child: self.to_do_service.toggle_child_completed(
                            item, child
                        ),
                        on_delete=lambda *_,
                        item=item,
                        child=child: self.to_do_service.delete_to_do_item_child(
                            item, child
                        ),
                    )
                )

        return elements

    def on_changed(self, *args):
        self.to_do_list.children = []
        elements = self.get_to_do_list_elements()
        self.to_do_list.children = elements

    def on_add_to_do(self, *args):
        text = self.to_do_text_entry.get_text()
        if self.parent_item is None:
            self.to_do_service.add_to_do_item(ToDoItemParent(text))
        else:
            self.to_do_service.add_child_to_item(self.parent_item, ToDoItem(text))
            self.parent_item = None
        self.to_do_text_entry.set_text("")
        self.toggle_view()

    def on_cancel_add_to_do(self, *args):
        self.to_do_text_entry.set_text("")
        self.toggle_view()

    def on_notify_text(self, *args):
        text = self.to_do_text_entry.get_text()
        if text is not None and text != "":
            self.add_button.set_sensitive(True)
        else:
            self.add_button.set_sensitive(False)
