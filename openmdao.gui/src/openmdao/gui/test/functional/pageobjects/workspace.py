import logging
import threading
import time

from nose import SkipTest
from nose.tools import eq_ as eq

from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import TimeoutException

from basepageobject import BasePageObject, TMO
from connections import ConnectionsPage
from dataflow import DataflowFigure
from editor import EditorPage
from elements import ButtonElement, InputElement, GridElement, TextElement
from util import abort, ValuePrompt, NotifierPage, ConfirmationPage


class WorkspacePage(BasePageObject):

    title_prefix = 'OpenMDAO:'

    # Top.
    project_menu      = ButtonElement((By.ID, 'project-menu'))
    save_button       = ButtonElement((By.ID, 'project-save'))
    run_button        = ButtonElement((By.ID, 'project-run'))
    reload_button     = ButtonElement((By.ID, 'project-reload'))
    close_button      = ButtonElement((By.ID, 'project-close'))
    exit_button       = ButtonElement((By.ID, 'project-exit'))

    view_menu         = ButtonElement((By.ID, 'view-menu'))
    cmdline_button    = ButtonElement((By.ID, 'view-cmdline'))
    console_button    = ButtonElement((By.ID, 'view-console'))
    files_button      = ButtonElement((By.ID, 'view-files'))
    library_button    = ButtonElement((By.ID, 'view-library'))
    objects_button    = ButtonElement((By.ID, 'view-components'))
    properties_button = ButtonElement((By.ID, 'view-properties'))
    workflow_button   = ButtonElement((By.ID, 'view-workflow'))
    dataflow_button   = ButtonElement((By.ID, 'view-dataflow'))
    refresh_button    = ButtonElement((By.ID, 'view-refresh'))

    tools_menu        = ButtonElement((By.ID, 'tools-menu'))
    editor_button     = ButtonElement((By.ID, 'tools-editor'))
    plotter_button    = ButtonElement((By.ID, 'tools-plotter'))
    addons_button     = ButtonElement((By.ID, 'tools-addons'))

    help_menu         = ButtonElement((By.ID, 'help-menu'))
    doc_button        = ButtonElement((By.ID, 'help-doc'))

    about_button      = ButtonElement((By.ID, 'about-item'))

    # Left side.
    objects_tab = ButtonElement((By.ID, 'otree_tab'))
    files_tab   = ButtonElement((By.ID, 'ftree_tab'))

    # Object context menu.
    obj_properties = ButtonElement((By.XPATH, "//a[(@rel='properties')]"))
    obj_dataflow   = ButtonElement((By.XPATH, "//a[(@rel='show_dataflow')]"))
    obj_workflow   = ButtonElement((By.XPATH, "//a[(@rel='show_workflow')]"))
    obj_run        = ButtonElement((By.XPATH, "//a[(@rel='run')]"))
    obj_toggle     = ButtonElement((By.XPATH, "//a[(@rel='toggle')]"))
    obj_remove     = ButtonElement((By.XPATH, "//a[(@rel='remove')]"))

    # File menu
    file_menu = ButtonElement((By.XPATH,
                           '/html/body/div/div/div/nav2/ul/li/a'))
    newfile_button = ButtonElement((By.XPATH,
                           '/html/body/div/div/div/nav2/ul/li/ul/li[1]/a'))
    newfolder_button = ButtonElement((By.XPATH,
                           '/html/body/div/div/div/nav2/ul/li/ul/li[2]/a'))
    add_button = ButtonElement((By.XPATH,
                           '/html/body/div/div/div/nav2/ul/li/ul/li[3]/a'))

    # File context menu.
    file_create = ButtonElement((By.XPATH, "//a[(@rel='createFile')]"))
    file_add    = ButtonElement((By.XPATH, "//a[(@rel='addFile')]"))
    file_folder = ButtonElement((By.XPATH, "//a[(@rel='createFolder')]"))
#    file_rename = ButtonElement((By.XPATH, "//a[(@rel='renameFile')]"))
#    file_view   = ButtonElement((By.XPATH, "//a[(@rel='viewFile')]"))
    file_edit   = ButtonElement((By.XPATH, "//a[(@rel='editFile')]"))
    file_import = ButtonElement((By.XPATH, "//a[(@rel='importFile')]"))
    file_exec   = ButtonElement((By.XPATH, "//a[(@rel='execFile')]"))
    file_delete = ButtonElement((By.XPATH, "//a[(@rel='deleteFile')]"))
    file_toggle = ButtonElement((By.XPATH, "//a[(@rel='toggle')]"))

    file_chooser = InputElement((By.ID, 'filechooser'))

    # Center.
    dataflow_tab = ButtonElement((By.ID, 'dataflow_tab'))
    workflow_tab = ButtonElement((By.ID, 'workflow_tab'))

    # Right side.
    properties_tab = ButtonElement((By.ID, 'properties_tab'))
    props_header   = TextElement((By.XPATH, "//div[@id='properties_pane']/h3"))
    props_inputs   = GridElement((By.XPATH, "//div[@id='properties_pane']/div[1]"))
    props_outputs  = GridElement((By.XPATH, "//div[@id='properties_pane']/div[2]"))

    library_tab    = ButtonElement((By.ID, 'library_tab'))
    library_search = InputElement((By.ID, 'objtt-select'))

    # Bottom.
    history = TextElement((By.ID, 'history'))
    command = InputElement((By.ID, 'command'))
    submit  = ButtonElement((By.ID, 'command-button'))

    def __init__(self, browser, port):
        super(WorkspacePage, self).__init__(browser, port)

        self.locators = {}
        self.locators["objects"] = (By.XPATH, "//div[@id='otree_pane']//li[@path]")
        self.locators["files"] = (By.XPATH, "//div[@id='ftree_pane']//a[@class='file ui-draggable']")

        # Wait for bulk of page to load.
        WebDriverWait(self.browser, 2*TMO).until(
            lambda browser: len(self.get_dataflow_figures()) > 0)
        # Now wait for WebSockets.
# FIXME: absolute delay before polling sockets.
        time.sleep(2)
        browser.execute_script('openmdao.Util.webSocketsReady(2);')
        NotifierPage.wait(self)

    def find_library_button(self, name):
        path = "//table[(@id='objtypetable')]//td[text()='%s']" % name
        for retry in range(5):
            try:
                element = WebDriverWait(self.browser, TMO).until(
                        lambda browser: browser.find_element(By.XPATH, path))
            except TimeoutException as err:
                logging.warning(str(err))
            else:
                break
        else:
            raise err

        return element

    def run(self, timeout=TMO):
        """ Run current component. """
        self('project_menu').click()
        self('run_button').click()
        NotifierPage.wait(self, timeout)

    def do_command(self, cmd, timeout=TMO):
        """ Execute a command. """
        self.command = cmd
        self('submit').click()
        NotifierPage.wait(self, timeout)

    def close_workspace(self, timeout=TMO):
        """ Close the workspace page. Returns :class:`ProjectsListPage`. """
        self.browser.execute_script('openmdao.Util.closeWebSockets();')
        NotifierPage.wait(self, timeout)
        self('project_menu').click()

        # Sometimes chromedriver hangs here, so we click in separate thread.
        # It's a known issue on the chromedriver site.
        closer = threading.Thread(target=self._closer)
        closer.daemon = True
        closer.start()
        closer.join(60)
        if closer.is_alive():
            abort(True)
            raise SkipTest("Can't close workspace, driver hung :-(")

        from project import ProjectsListPage
        return ProjectsListPage.verify(self.browser, self.port)

    def _closer(self):
        """ Clicks the close button. """
        self('close_button').click()

    def open_editor(self):
        """ Open code editor.  Returns :class:`EditorPage`. """
        self('tools_menu').click()
        self('editor_button').click()
        self.browser.switch_to_window('Code Editor')
        return EditorPage.verify(self.browser, self.port)


    def get_files(self):
        """ Return names in the file tree. """
        WebDriverWait(self.browser, TMO).until(
            lambda browser: browser.find_element(By.ID, 'ftree_pane'))
# FIXME: absolute delay for tree population.
        time.sleep(1)
        file_items = self.browser.find_elements(*self.locators["files"])
        file_names = []
        for i in range(len(file_items)):
            for retry in range(10):  # This has had issues...
                try:
                    file_names.append(self.browser.find_elements(*self.locators["files"])[i].text.strip())
                except StaleElementReferenceException:
                    logging.warning('get_files: StaleElementReferenceException')
                else:
                    break
        return file_names

    def add_file(self, file_path):
        """ Read in `file_path` """
        if file_path.endswith('.pyc'):
            file_path = file_path[:-1]

        self('file_menu').click()
        self('add_button').click()

        self.file_chooser = file_path

    def new_file_dialog(self):
        """ bring up the new file dialog """
        self('files_tab').click()
        self('file_menu').click()
        self('newfile_button').click()
        page = ValuePrompt(self.browser, self.port)
        return page

    def edit_file(self, filename, dclick=True):
        """ Edit `filename` via double-click or context menu. """
        self('files_tab').click()
        xpath = "//a[(@path='/%s')]" % filename
        element = WebDriverWait(self.browser, TMO).until(
            lambda browser: browser.find_element_by_xpath(xpath))
        chain = ActionChains(self.browser)
        if dclick:  # This has had issues...
            for i in range(10):
                try:
                    chain.double_click(element).perform()
                except StaleElementReferenceException:
                    logging.warning('edit_file: StaleElementReferenceException')
                    element = WebDriverWait(self.browser, 1).until(
                        lambda browser: browser.find_element_by_xpath(xpath))
                    chain = ActionChains(self.browser)
                else:
                    break
        else:
            chain.context_click(element).perform()
            self('file_edit').click()
        self.browser.switch_to_window('Code Editor')
        return EditorPage.verify(self.browser, self.port)

    def save_project(self):
        """ Save current project. """
        self('project_menu').click()
        self('save_button').click()
        NotifierPage.wait(self)

    def get_objects_attribute(self, attribute, visible=False):
        """ Return list of `attribute` values for all objects. """
        WebDriverWait(self.browser, TMO).until(
            lambda browser: browser.find_element(By.ID, 'otree_pane'))
        object_elements = self.browser.find_elements(*self.locators["objects"])
        values = []
        for element in object_elements:
            if not visible or element.is_displayed():
                values.append(element.get_attribute(attribute))
        return values

    def select_object(self, component_name):
        """ Select `component_name`. """
        self('objects_tab').click()
        xpath = "//div[@id='otree_pane']//li[(@path='%s')]//a" % component_name
        element = WebDriverWait(self.browser, TMO).until(
                      lambda browser: browser.find_element_by_xpath(xpath))
        element.click()

    def expand_object(self, component_name):
        """ Expands `component_name`. """
        self('objects_tab').click()
        xpath = "//div[@id='otree_pane']//li[(@path='%s')]//ins" % component_name
        element = WebDriverWait(self.browser, TMO).until(
                      lambda browser: browser.find_element_by_xpath(xpath))
        element.click()
        time.sleep(1)  # Wait for cute animation.

    def show_dataflow(self, component_name):
        """ Show dataflow of `component_name`. """
        self('objects_tab').click()
        xpath = "//div[@id='otree_pane']//li[(@path='%s')]//a" % component_name
        element = WebDriverWait(self.browser, TMO).until(
                      lambda browser: browser.find_element_by_xpath(xpath))
        element.click()
        time.sleep(0.5)
        # Try to recover from context menu not getting displayed.
        for retry in range(3):
            chain = ActionChains(self.browser)
            chain.context_click(element).perform()
            try:
                self('obj_dataflow').click()
                break
            except TimeoutException:
                if retry >= 2:
                    raise

    def show_library(self):
        # For some reason the first try never works, so the wait is set
        # low and we expect to retry at least once.
        for retry in range(5):
            try:
                self('library_tab').click()
                WebDriverWait(self.browser, 1).until(
                    lambda browser: self('library_search').is_visible())
            except TimeoutException:
                if retry:
                    logging.warning('TimeoutException in show_library')
            else:
                break
        else:
            raise RuntimeError('Too many TimeoutExceptions')

    def get_library_item(self, item_name):
        """ Return element for library item `item_name`. """
        xpath = "//table[(@id='objtypetable')]//td[(@modpath='%s')]" % item_name
        library_item = WebDriverWait(self.browser, TMO).until(
            lambda browser: browser.find_element_by_xpath(xpath))
        WebDriverWait(self.browser, TMO).until(
            lambda browser: library_item.is_displayed())
# FIXME: absolute delay to wait for 'slide' to complete.
        time.sleep(1)
        return library_item

    def add_library_item_to_dataflow(self, item_name, instance_name, check=True):
        """ Add component `item_name`, with name `instance_name`. """
        library_item = self.get_library_item(item_name)

        target = WebDriverWait(self.browser, TMO).until(
            lambda browser: browser.find_element_by_xpath("//*[@id='-dataflow']"))

        chain = ActionChains(self.browser)
        if False:
            chain = chain.drag_and_drop(library_item, target)
        else:
            chain = chain.click_and_hold(library_item)
            chain = chain.move_to_element_with_offset(target, 100, 100)
            chain = chain.release(None)
        chain.perform()

        page = ValuePrompt(self.browser, self.port)
        page.set_value(instance_name)
        # Check that the prompt is gone so we can distinguish a prompt problem
        # from a dataflow update problem.
        time.sleep(0.25)
        self.browser.implicitly_wait(1) # We don't expect to find anything.
        try:
            eq(len(self.browser.find_elements(*page('prompt')._locator)), 0)
        finally:
            self.browser.implicitly_wait(TMO)

        if check:  # Check that it's been added.
            WebDriverWait(self.browser, TMO).until(
                lambda browser: instance_name in self.get_dataflow_component_names())

    def get_dataflow_figures(self):
        """ Return dataflow figure elements. """
        time.sleep(0.5)  # Pause for stable display.
        return self.browser.find_elements_by_class_name('DataflowFigure')

    def get_dataflow_figure(self, name, prefix=None, retries=5):
        """ Return :class:`DataflowFigure` for `name`. """
        for retry in range(retries):
            time.sleep(0.5)  # Pause for stable display.
            figures = self.browser.find_elements_by_class_name('DataflowFigure')
            if not figures:
                continue
            fig_name = None
            for figure in figures:
                self.browser.implicitly_wait(1)
                try:
                    header = figure.find_elements_by_class_name('DataflowFigureHeader')
                    if len(header) == 0:
                        # the outermost figure (globals) has no header or name
                        if name == '' and prefix is None:
                            fig = DataflowFigure(self.browser, self.port, figure)
                            return fig
                        else:
                            continue
                    fig_name = figure.find_elements_by_class_name('DataflowFigureHeader')[0].text
                except StaleElementReferenceException:
                    logging.warning('get_dataflow_figure:'
                                    ' StaleElementReferenceException')
                else:
                    if fig_name == name:
                        fig = DataflowFigure(self.browser, self.port, figure)
                        if prefix is not None:
                            if prefix:
                                fig.pathname = '%s.%s' % (prefix, name)
                            else:
                                fig.pathname = name
                        return fig
                finally:
                    self.browser.implicitly_wait(TMO)
        return None

    def get_dataflow_component_names(self):
        """ Return names of dataflow components. """
        names = []

        # Assume there should be at least 1, wait for number to not change.
        n_found = 0
        for retry in range(10):
            time.sleep(0.5)  # Pause for stable display.
            dataflow_component_headers = \
                self.browser.find_elements_by_class_name('DataflowFigureHeader')
            if dataflow_component_headers:
                n_headers = len(dataflow_component_headers)
                if n_found:
                    if n_headers == n_found:
                        break
                n_found = n_headers
        else:
            logging.error('get_dataflow_component_names: n_found %s', n_found)
            return names

        for i in range(len(dataflow_component_headers)):
            for retry in range(10):  # This has had issues...
                try:
                    names.append(self.browser.find_elements_by_class_name('DataflowFigureHeader')[i].text)
                except StaleElementReferenceException:
                    logging.warning('get_dataflow_component_names:'
                                    ' StaleElementReferenceException')
                except IndexError:
                    logging.warning('get_dataflow_component_names:'
                                    ' IndexError for i=%s, headers=%s',
                                    i, len(dataflow_component_headers))
                else:
                    break

        if len(names) != len(dataflow_component_headers):
            logging.error('get_dataflow_component_names:'
                          ' expecting %d names, got %s',
                          len(dataflow_component_headers), names)
        return names

    def connect(self, src, dst):
        """ Return :class:`ConnectionsPage` for connecting `src` to `dst`. """
        chain = ActionChains(self.browser)
        chain = chain.click_and_hold(src.output_port)
        # Using root rather than input_port since for some reason
        # even using a negative Y offset can select the parent's input.
        chain = chain.move_to_element(dst.input_port)
        chain = chain.release(None)
        chain.perform()
        parent, dot, srcname = src.pathname.rpartition('.')
        parent, dot, dstname = dst.pathname.rpartition('.')
        editor_id = 'ConnectionsFrame-%s' % (parent)
        editor_id = editor_id.replace('.', '-')
        return ConnectionsPage(self.browser, self.port, (By.ID, editor_id))

    def replace(self, name, classname, confirm=True):
        """ Replace `name` with an instance of `classname`. """
        library_item = self.get_library_item(classname)
        target = self.get_dataflow_figure(name).root

        chain = ActionChains(self.browser)
        chain = chain.click_and_hold(library_item)
        chain = chain.move_to_element_with_offset(target, 125, 30)
        chain = chain.release(None)
        chain.perform()

        dialog = ConfirmationPage(self)
        if confirm:
            dialog.click_ok()
        else:
            dialog.click_cancel()

    def hide_left(self):
        toggler = self.browser.find_element_by_css_selector('.ui-layout-toggler-west-open')
        toggler.click()

    def show_left(self):
        toggler = self.browser.find_element_by_css_selector('.ui-layout-toggler-west-closed')
        toggler.click()

    def hide_right(self):
        toggler = self.browser.find_element_by_css_selector('.ui-layout-toggler-east-open')
        toggler.click()

    def show_right(self):
        toggler = self.browser.find_element_by_css_selector('.ui-layout-toggler-east-closed')
        toggler.click()

    def hide_console(self):
        toggler = self.browser.find_element_by_css_selector('.ui-layout-toggler-south-open')
        toggler.click()

    def show_console(self):
        toggler = self.browser.find_element_by_css_selector('.ui-layout-toggler-south-closed')
        toggler.click()
