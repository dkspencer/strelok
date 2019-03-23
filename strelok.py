"""
STRELOK: Automated Open-Source Intelligence
Copyright (C) 2018  Danielle Spencer

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""

import gi  # GTK library
import time
import webbrowser  # Opening the User Manual
import pickle  # Dumping/loading website cookies
import os  # Operating system interaction
import re  # Formatting lists and locating html elements
import itertools  # Flatten temp_occupants_list
import configparser  # Configuration file parser
import logging  # Module logger to file
from threading import Thread  # Multithreading
from selenium import webdriver  # Browser automation
from selenium.webdriver.chrome.options import Options  # Hide the browser
from selenium.webdriver.common.keys import Keys  # Selenium keyboard input
import selenium.webdriver.support.ui as ui  # Refreshing browser
from selenium.common.exceptions import ElementNotVisibleException
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from bs4 import BeautifulSoup  # Website scraper
gi.require_version('Gtk', '3.0')  # Version of GTK+
from gi.repository import GLib, Gtk, GObject  # GUI and Threading

# All references to builder.get_object refer to getting the objects
# from the .XML Glade GUI file.

# Set the default logging level - will log everything DEBUG and above.
logging.basicConfig(filename='strelok.log', level=logging.DEBUG,
                    format='%(asctime)s:%(levelname)s:%(message)s')

# Ready Strelok for the threads
GObject.threads_init()

# Builder is used for importing the GTK GUI XML
builder = Gtk.Builder()
builder.add_from_file("strelok.glade")
application_window = builder.get_object("ApplicationWindow")

progress_bar = builder.get_object("progress_bar")

# Check if required files exist - if not, create them.
if not os.path.exists('facebook_cookies'):
    open('facebook_cookies', 'w+').close()
if not os.path.exists('linkedin_cookies'):
    open('linkedin_cookies', 'w+').close()
if not os.path.exists('.config.ini'):
    # Default settings for config.ini file
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'TimeSleep': '0.5',
                         'SaveCreds': 'No',
                         'EULA': 'No',
                         'LinkedIn': 'No'}
    config['SECURITY'] = {}
    config['SECURITY'] = {'Key': ''}
    config['WEBSITES'] = {}
    config['WEBSITES'] = {'FacebookUser': '',
                          'FacebookPass': '',
                          'LinkedInUser': '',
                          'LinkedInPass': ''}
    with open('.config.ini', 'w') as configfile:
        config.write(configfile)

# Read config file - for use later
if os.path.exists('.config.ini'):
    config = configparser.ConfigParser()
    config.read('.config.ini')


class EULA_Assistant:

    """ This class deals with the EULA Assistant that appears the first
    time the user starts Strelok on a new computer/new folder.
    It includes:
    * PAGE 1 Key authentication
    * PAGE 2 Open source license agreement
    * PAGE 3 Summary page

    Temporary verification key: F4FL6NXJZZ9PMW81

    """

    # Checks if the EULA has been accepted/key exists in config.ini
    if (config['DEFAULT']['EULA'] == "No" or
            config['SECURITY']['Key'] != "F4FL6NXJZZ9PMW81"):

        def verify_button(self):

            """ Clicking the Verify button will check the product key
            against the hard coded key in the source code.
            The key will then be saved in the config.ini file.

            """

            # Get the key error and key verified "boxes" from the XML
            key_error = builder.get_object("key_error_box")
            key_verified = builder.get_object("key_verify_box")

            # Get the text from the product key text entry box
            key_entry = builder.get_object("key_entry")
            product_key = key_entry.get_text()

            # Check if the product key is a match
            if product_key == "F4FL6NXJZZ9PMW81":

                # Hide the invalid product key error
                # (incase they previous entered an incorrect key)
                key_error.hide()

                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " Key verified")

                # Show the product key confirmation message
                # when the user enters the correct key
                key_verified.show_all()

                # Save users product key to the .config.ini file.
                config.set('SECURITY', 'Key', product_key)
                with open('.config.ini', 'w') as configfile:
                    config.write(configfile)

                # Activate the assistant button when the correct product key
                # has been verified.
                EULA_Assistant.assistant.set_page_complete(
                    EULA_Assistant.activation_page, True)
            else:
                # Inform the user they entered the wrong Product Key.
                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " Key incorrect")

                # Hide the correct product key message
                key_verified.hide()

                # Show the invalid product key message
                key_error.show_all()

        def on_cancel_clicked(self):

            """ Clicking the Cancel button will exist Strelok

            """

            Gtk.main_quit()

        def on_close_clicked(self):

            """ Clicking Closewill close the assistant
            but keep Strelok open.
            """

            EULA_Assistant.assistant.hide()

        def on_eula_agreement(self):

            """ Selecting the checkbox ("I agree") will let the user
            move forward.
            It will also save that they have agreed to the EULA in
            the .config.ini file.

            """

            EULA_Assistant.assistant.set_page_complete(
                EULA_Assistant.eula_page,
                EULA_Assistant.eula_checkbox.get_active())

            # Save users agreement to .config.ini
            config.set('DEFAULT', 'EULA', "Yes")
            with open('.config.ini', 'w') as configfile:
                config.write(configfile)

        # Displays the EULA assistant - includes key activation & EULA
        assistant = builder.get_object("eula_assistant")
        assistant.show_all()

        # Hide the Key Error box/Key Error label immediately on start.
        key_error_box = builder.get_object("key_error_box")
        key_error_box.hide()

        # Hide the Key Verified box/Key Error label immediately on start.
        key_verify_box = builder.get_object("key_verify_box")
        key_verify_box.hide()

        # Get the "assistant action area" - (assistant buttons)
        assistant_buttons = builder.get_object("assistant_buttons")

        # Connect the assistant buttons to functions
        assistant.connect("cancel", on_cancel_clicked)
        assistant.connect("close", on_close_clicked)

        # Connect the "I agree" checkbox with the on_checkbox function.
        eula_checkbox = builder.get_object("eula_checkbox")
        eula_checkbox.connect("toggled", on_eula_agreement)

        # Get assistant pages from the XML
        activation_page = builder.get_object("activation_page")
        eula_page = builder.get_object("eula_page")
        summary_page = builder.get_object("summary_page")

        # The Summary page will automatically let the user
        # use the assistant buttons.
        assistant.set_page_complete(summary_page, True)

    else:
        def verify_button(self):

            """
            For some reason, having this here works...
            It's no longer complaining that the verify_button
            function not existing. So I left it as a "pass"
            because it has no intended function outside
            of the EULA_Assistant class.
            """

            pass

        # Pass because the EULA & Product Key have been done.
        pass


class Config:

    """ This class deals with the "CONFIG" section of Strelok.
    It includes;
    * Time.sleep settings
    * Save Changes & Revert Changes buttons
    * Populating usernames and passwords from .config.ini
    * Website usernames and passwords

    """

    # The sleep variable changes all the time.sleep() throughout the program.
    # It can be increased by the user by changing the 'timesleep =' in the
    # .config.ini file.
    # Its purpose is to allow slower computers/Internet connections
    if config['DEFAULT']['TimeSleep'] != "0.5":
        sleep = int(config['DEFAULT']['TimeSleep'])
    else:
        sleep = 0.5

    # Get the Time Delay spinbutton from the XML
    time_delay = builder.get_object("time_delay_button")

    # Set the value from of the time delay spinbutton to that in .config.ini
    time_delay.set_value(float(sleep))

    # Check if SaveCreds is enabled in .config.ini
    if config['DEFAULT']['SaveCreds'] == "Yes":
        SaveCreds = True
        save_check = builder.get_object("save_check")
        save_check.set_active(True)
    else:
        SaveCreds = False

    linkedin_check = builder.get_object("linkedin_check")

    # Check if 'linkedin' is Yes in the .config.ini file, and set the
    # LinkedIn checkbox accordingly
    if config['DEFAULT']['linkedin'] == "Yes":
        linkedin_check.set_active(True)
    else:
        linkedin_check.set_active(False)

    # Get objects from GTK .XML file
    facebookuser_entry = builder.get_object("facebook_username")
    facebookpass_entry = builder.get_object("facebook_password")
    linkedinuser_entry = builder.get_object("linkedin_username")
    linkedinpass_entry = builder.get_object("linkedin_password")

    # Usernames and Passwords used to log into websites.
    facebook_username = ""
    facebook_password = ""

    linkedin_username = ""
    linkedin_password = ""

    # Load usernames and passwords from .config.ini file
    facebookuser_entry.set_text(config['WEBSITES']['FacebookUser'])
    facebookpass_entry.set_text(config['WEBSITES']['FacebookPass'])
    linkedinuser_entry.set_text(config['WEBSITES']['LinkedInUser'])
    linkedinpass_entry.set_text(config['WEBSITES']['LinkedInPass'])

    # Set variable from .config.ini to username and password variables
    facebook_username = config['WEBSITES']['FacebookUser']
    facebook_password = config['WEBSITES']['FacebookPass']
    linkedin_username = config['WEBSITES']['LinkedInUser']
    linkedin_password = config['WEBSITES']['LinkedInPass']

    def revert_changes(self):

        """ When Revert Changes button is clicked, revert to
        previously saved credentials found in config.ini and
        add to approriate text entry boxes

        """

        Config.facebookuser_entry.set_text(Config.facebook_username)
        Config.facebookpass_entry.set_text(Config.facebook_password)

        Config.linkedinuser_entry.set_text(Config.linkedin_username)
        Config.linkedinpass_entry.set_text(Config.linkedin_password)

    def save_changes(self):

        """ When Save Changes button is clicked, save the text
        from the text entry boxes either to the variable or the
        variable and the config.ini.

        """

        output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                             " Changes saved!\n")

        # Set username & password variables
        Config.facebook_username = Config.facebookuser_entry.get_text()
        Config.facebook_password = Config.facebookpass_entry.get_text()
        Config.linkedin_username = Config.linkedinuser_entry.get_text()
        Config.linkedin_password = Config.linkedinpass_entry.get_text()

        # Get the Permanent Save checkbox from the XML
        save_check = builder.get_object("save_check")

        timesleep = Config.time_delay.get_value()

        linkedin_check = builder.get_object("linkedin_check")

        if linkedin_check.get_active():
            config.set('DEFAULT', 'linkedin', "Yes")
        else:
            config.set('DEFAULT', 'linkedin', "No")

        # If the checkbox is active, save the entry boxes to .config.ini file.
        if save_check.get_active():
            output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                 " Changes saved to config.ini")
            config.set('WEBSITES', 'facebookuser', Config.facebook_username)
            config.set('WEBSITES', 'facebookpass', Config.facebook_password)
            config.set('WEBSITES', 'linkedinuser', Config.linkedin_username)
            config.set('WEBSITES', 'linkedinpass', Config.linkedin_password)
            config.set('DEFAULT', 'SaveCreds', "Yes")
            config.set('DEFAULT', 'timesleep', str(timesleep))
            with open('.config.ini', 'w') as configfile:
                config.write(configfile)


class Results:

    """ This class deals with the Results table (the big
    white center).
    It includes;
    * Treeview and Liststore
    * Open Link, Delete Link and Clear buttons

    """

    content_box = builder.get_object("content_box")
    scrolled_window = builder.get_object("content_scrolled_window")
    liststore = Gtk.ListStore(str, str, str)

    treeview = Gtk.TreeView(liststore)
    for i, column_title in enumerate(["Page Name", "Website Name",
                                      "Website URL"]):
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(column_title, renderer, text=i)
        column.set_resizable(False)
        column.set_min_width(150)
        column.set_expand(True)
        treeview.append_column(column)

    scrolled_window.add(treeview)

    treeselection = treeview.get_selection()
    treeselection.set_mode(Gtk.SelectionMode.SINGLE)

    def open_link_button(self):

        """ Open a selected item in the browser

        """

        (model, iter) = Results.treeselection.get_selected_rows()
        for path in iter:
            iter = model.get_iter(path)
            value = model.get_value(iter, 2)
            webbrowser.open(value, new=2)

    def delete_link_button(self):

        """ Delete a selected item in the treeview

        """

        (model, iter) = Results.treeselection.get_selected_rows()
        for path in iter:
            iter = model.get_iter(path)
            Results.liststore.remove(iter)

    def clear_button(self):

        """ When Clear button is pressed

        """

        Results.liststore.clear()


class Search:

    """
    This class deals with the main feature - Search. It includes;
    * Name, Location & Known Friend text boxes
    * Search & Clear buttons
    * 192 search
    * Facebook search
    * LinkedIn search
    * Progress bar
    * Scraping
    * Facebook Graph search

    """

    # Get the objects from the Glade XML
    search_error = builder.get_object("search_error")
    facebook_error = builder.get_object("facebook_error")
    friends_entry = builder.get_object("friends_entry")
    name_entry = builder.get_object("name_entry")
    location_entry = builder.get_object("location_entry")
    not_found_192 = builder.get_object("192_error")
    email_entry = builder.get_object("email_entry")
    work_entry = builder.get_object("workplace_entry")
    school_entry = builder.get_object("school_entry")

    # Bool used to prevent multiple progress bar threads from starting
    progress_bar = False

    # These websites are used by Selenium, for initial navigation to
    websites = ["http://www.192.com", "https://facebook.com",
                "https://uk.linkedin.com/"]

    # Names from 192.com - 'other occupants'
    occupants_list = []

    # Constants used for the different functions in this class

    # search_facebook/profile_loop function
    profile_dynamic = 0

    # The URL, persons name and ID of the Facebook profile (if found)
    # search_facebook/friends_loop
    facebook_profile_url = ""
    profile_name = ""
    profile_id = ""

    # List for Facebook profiles' work and education
    profile_info = []

    # Ignore list contains all the 'href' elements to ignore in the
    # profile results search page.
    ignore_list = ["https://www.linkedin.com/legal/cookie-policy",
                   "/psettings/presence"]

    # Bool used to determine how long to keep searching for profiles
    iterating_profiles = True

    # Facebook ignore href list - used in the profile search page
    profile_ignore_list = []

    def clear_button(self):

        """ When Clear button is clicked, clear:
        * Target name
        * Target location
        * Known friend

        """

        Search.name_entry.set_text("")
        Search.location_entry.set_text("")
        Search.friends_entry.set_text("")

    def search_button(self):

        """ When the search button is clicked, search:
        * 192
        * Facebook
        * LinkedIn

        """

        # Retreive the text from the entry boxes
        known_friend = Search.friends_entry.get_text()
        target_name = Search.name_entry.get_text()
        target_loc = Search.location_entry.get_text()
        target = target_name + " + " + target_loc

        def search_192():

            """ Selenium WebDriver will search 192.com using the
            provided target name and location - then it will retreive
            the other occupants name fields if results found.

            """

            output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                 " Starting the search for " +
                                 target_name.title() + " from " +
                                 target_loc.title() +
                                 " on 192.com \n")

            # Set Chrome options to hide the browser window
            CHROME_PATH = '/usr/bin/google-chrome'
            CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
            #WINDOW_SIZE = "1920,1080"

            chrome_options = Options()
            #chrome_options.add_argument("--headless")
            #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
            chrome_options.binary_location = CHROME_PATH

            driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                      chrome_options=chrome_options
                                     )

            # Go to 192.com
            driver.get(Search.websites[0])

            # so many lists, need to figured out how to get fewer
            temp_list = []
            new_list = []
            temp_occupants = []

            try:
                # Find the Name text entry.
                search_person = driver.find_element_by_id("name")
                search_person.send_keys(target_name)

                # Find the Location text entry.
                search_person = driver.find_element_by_id("location")
                search_person.send_keys(target_loc)

                search_person.send_keys(Keys.RETURN)

            # Inform the user/close the browser if text fields can't be found.
            except:
                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     "Name and Location field on 192 cannot" +
                                     "be found \n")
                driver.close()
                return

            # Beautifulsoup - get the page source
            time.sleep(Config.sleep)
            html = driver.page_source
            soup = BeautifulSoup(html, "lxml")

            # Close the browser - no longer needed
            driver.close()

            # Check for text "Can't find the person you are looking for?"
            if soup.find_all("div", text="Can't find the person you" +
                             " are looking for?"):
                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " [192] No search results for " +
                                     target_name.title() + " from " +
                                     target_loc.title() + " \n")
                
                # Signal the progress bar to stop
                progress_bar = builder.get_object("progress_bar")
                progress_bar.set_text("Finished!")
                progress_bar.set_pulse_step(0.00)

                return

            else:
                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " [192] Search results for " +
                                     target_name.title() +
                                     " from " +
                                     target_loc.title() + "\n")

                # Format the extracted text using regular expressions
                for occupants in soup.find_all('div', attrs={"class":
                                               "contentWrapper coocupants"}):

                    # Get strings from page
                    friends_string = occupants.get_text()

                    # Remove white spaces
                    friends_string = re.sub(r'[\s+]', '', friends_string)

                    # Add spaces before capital letters
                    friends_string = re.sub(r"(?<=\w)([A-Z])", r" \1",
                                            friends_string)

                    # Add string to list
                    temp_list.append(friends_string)

                # Remove empty items in list
                temp_list = list(filter(None, temp_list))

                # Separate names in the list
                new_list = [x.split(',') for x in temp_list]

                # Flattern the lists to combine first and last name
                temp_occupants = list(itertools.chain.from_iterable(new_list))

                # Split names into a list of list
                for name in temp_occupants:
                    Search.occupants_list = [name.split(' ') for name in
                                             temp_occupants]

                # Check if list of list contains more than 3 words
                # and delete the second word.
                # This is because we don't need the middle name initial
                for name in Search.occupants_list:
                    if len(name) >= 3:
                        del name[1]

                # Print results in the OUTPUT text box
                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " Search results are: " +
                                     str(Search.occupants_list) + "\n")

                # Call the search_facebook function if results found
                search_facebook()

        def search_facebook():

            """ This function tells Selenium WebDriver to go to;
            * Go to Facebook.com
            * Search for the target name and location
            * Loop through results
            * Loop through friends
            * Scrape data
            * Get Facebook Graph data
            * Add to Results

            """

            # Set Chrome options to hide the browser window
            CHROME_PATH = '/usr/bin/google-chrome'
            CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
            #WINDOW_SIZE = "1920,1080"

            chrome_options = Options()
            #chrome_options.add_argument("--headless")
            #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
            prefs = {"profile.default_content_setting_values.notifications": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            chrome_options.binary_location = CHROME_PATH

            driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                      chrome_options=chrome_options
                                     )

            # Chrome option to prevent the notifications dialog from popping up
            #chrome_options = webdriver.ChromeOptions()
            #prefs = {"profile.default_content_setting_values.notifications": 2}
            #chrome_options.add_experimental_option("prefs", prefs)
            #driver = webdriver.Chrome('/usr/bin/chromedriver',
            #chrome_options=chrome_options)

            # Go to Facebook.com
            driver.get(Search.websites[1])

            output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                 " Starting Selenium WebDriver \n")

            # Check if Facebook cookies is not empty and add to browser
            if os.stat('facebook_cookies').st_size != 0:

                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " Facebook cookies have been found" +
                                     "adding to browser\n")

                with open('facebook_cookies', 'rb') as cookiefile:
                    cookies = pickle.load(cookiefile)
                    for cookie in cookies:
                        driver.add_cookie(cookie)

                driver.refresh()

            # Check if Facebook cookies is empty and log into Facebook
            elif os.stat('facebook_cookies').st_size == 0:

                output_buffer.insert(output_iter, time.strftime("%H:%M:%S") +
                                     " No Facebook cookies have been found\n")

                # Start the loop for finding the password field
                # note: sometimes not visible
                finding_elements = True
                while finding_elements:

                    try:
                        password_element = driver.find_element_by_id("pass")

                    except ElementNotVisibleException:
                        driver.refresh()

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Facebook Password field not " +
                                             "not visible, refreshing page.\n")
                        
                        # Signal the progress bar to stop
                        progress_bar = builder.get_object("progress_bar")
                        progress_bar.set_text("Finished!")
                        progress_bar.set_pulse_step(0.00)

                    else:
                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Entering Facebook username"
                                             " and password\n")

                        username_element = driver.find_element_by_id("email")
                        username_element.send_keys(Config.facebook_username)
                        password_element.send_keys(Config.facebook_password)
                        password_element.send_keys(Keys.RETURN)

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Logging into Facebook \n")

                        time.sleep(Config.sleep)
                        html = driver.page_source
                        soup = BeautifulSoup(html, "lxml")

                        if soup.find_all("span", text="Log in to Facebook"):

                            driver.close()

                            # Signal the progress bar to stop
                            progress_bar = builder.get_object("progress_bar")
                            progress_bar.set_text("Finished!")
                            progress_bar.set_pulse_step(0.00)

                            output_buffer.insert(output_iter,
                                                 time.strftime("%H:%M:%S") +
                                                 " Cannot log into Facebook" +
                                                 ", incorrect login details.\n")

                            return

                        else:
                            output_buffer.insert(output_iter,
                                                 time.strftime("%H:%M:%S") +
                                                 " Dumping Facebook cookies" +
                                                 " into facebook_cookies\n")

                            # Add cookies to the facebook_cookies file
                            with open('facebook_cookies', 'wb') as filehandler:
                                pickle.dump(driver.get_cookies(), filehandler)

                            # End the loop
                            finding_elements = False

            def search_bar():

                """ Selenium WebDriver will find the search bar and enter
                the targets "name + location"

                """

                # Loop that finds the search bar element "q" and enters
                # text and checks if the element goes stale - to then
                # reaquire the element to proceed.
                searching_for_element = True
                while searching_for_element:
                    try:
                        query_elem = driver.find_element_by_name("q")

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Found the Facebook search" +
                                             "box, entering targets' name" +
                                             " and location\n")

                        query_elem.send_keys(target)
                        query_elem.send_keys(Keys.RETURN)

                    # Check if the element "q" goes stale and reaquire.
                    except StaleElementReferenceException:
                        query_elem = driver.find_element_by_name("q")
                        query_elem.send_keys(Keys.RETURN)

                    # Check if the search history drop-down does not
                    # disappear, if so press ESCAPE to hide.
                    # Bad practice but specific error cannot be determined.
                    except:
                        query_elem.send_keys(Keys.ESCAPE)

                    # End the loop
                    searching_for_element = False

                # Call the next function to continue.
                people_button()

            def people_button():

                """ Selenium WebDriver will find and click the
                People button, to go to the people results page.

                """

                # Delay BeautifulSoup getting the page source
                time.sleep(Config.sleep + 1.5)

                # Tell BeautifulSoup to get the page source
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # List containing all the 'fetchstream' element names
                fetchstream_list = []

                # Find all the 'fetchstream' element names and add to
                # the fetchstream_list.
                for elements in soup.findAll('div',
                                             id=re.compile("u_fetchstream_")):
                    fetchstream_list.append(elements['id'])

                # Loop through the fetchstream_list --> create the xpath and
                # try clicking the element.
                search_for_element = True
                while search_for_element:
                    for element in fetchstream_list:
                        xpath = ("//*[@id='" + element +
                                 "']/div/div/div/ul/li[3]/a")
                        try:
                            driver.find_element_by_xpath(xpath).click()
                        except NoSuchElementException:
                            pass
                        else:
                            search_for_element = False
                            break
                    break

                # If the fetchstream list is empty, try the u_0_ element name
                if not fetchstream_list:

                    # List containing all 'u_0_ ...' element names
                    u_0_list = []

                    # Find all the 'u_0_' elements on page
                    for elements in soup.findAll('div', id=re.compile("u_0_")):
                        u_0_list.append(elements['id'])

                    # Loop through the u_0_list, create the xpath and
                    # try clicking the element.
                    search_for_element = True
                    while search_for_element:
                        for element in u_0_list:
                            xpath = ("//*[@id='" + element +
                                     "']/div/div/div/ul/li[3]/a")
                            try:
                                driver.find_element_by_xpath(xpath).click()
                            except NoSuchElementException:
                                pass
                            else:
                                search_for_element = False
                                break
                        break

                # Call the next function to continue.
                profile_loop()

            def profile_loop():

                """ Iterate through profiles using the 'data-testid'
                element name.

                """

                # Delay BeautifulSoup getting the page source
                time.sleep(Config.sleep + 0.5)

                # Tell BeautifulSoup to get the page source
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # List containing all the 'fetchstream' element names
                fetchstream_list = []

                print ("profile loop" + str(fetchstream_list))

                # Find all the 'fetchstream' element names and add to
                # the fetchstream_list.
                for elements in soup.findAll('div', id=re.compile
                                             ("u_ps_fetchstream_")):
                    fetchstream_list.append(elements['id'])

                # For items in fetchstream list, check if the full
                # xpath exists on page and click it.
                for element in fetchstream_list:

                    # As this function will be called once and then reverted
                    # back to multiple times.
                    # This IF statement acts as a gate for deciding whether
                    # to continue if the profile has been found in the scrape
                    # function.
                    if Search.iterating_profiles is True:

                        # Create the complete xpath
                        xpath = ("//*[@id='" + element +
                                 "']/div/div/div/div[1]/div[2]/div/div/div/a")

                        # Try finding the xpath on the page
                        try:
                            profile_link = driver.find_element_by_xpath(xpath)

                        # If xpath not found, pass and go to the next item in
                        # the fetchstream list.
                        except NoSuchElementException:
                            pass

                        # If xpath is found, carry on.
                        else:
                            # Get the profile_link elements href attribute
                            profile_href = profile_link.get_attribute("href")

                            # Check if the href attribute has previous been
                            # found - pass if it has.
                            if profile_href in Search.profile_ignore_list:
                                pass

                            else:
                                # Add the href attribute to the ignore list for
                                # future references
                                Search.profile_ignore_list.append(profile_href)

                                # Click the profile link
                                profile_link.click()

                                # driver.execute_script("window.history.go(-1)")

                                # Call the friends_button function
                                friends_button()
                    else:
                        pass

            def friends_button():

                """ Selenium WebDriver will click the Friends button on
                the targets profile.

                """

                # Delay BeautifulSoup getting the page source
                time.sleep(Config.sleep)

                # Tell BeautifulSoup to get the page source
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # Get the current URL, incase this is the correct profile.
                Search.facebook_profile_url = driver.current_url

                # List containing all the 'fetchstream' element names
                fetchstream_list = []

                # Find all the 'fetchstream' element names and add to
                # the fetchstream_list.
                for elements in soup.findAll('ul', id=re.compile
                                             ("u_fetchstream_")):
                    fetchstream_list.append(elements['id'])

                # Loop through the fetchstream_list and create the
                # xpath and try clicking the element.
                search_for_element = True
                while search_for_element:
                    for xpath in fetchstream_list:
                        element = "//*[@id='" + xpath + "']/li[3]/a"
                        try:
                            driver.find_element_by_xpath(element).click()
                        except NoSuchElementException:
                            pass
                        else:
                            search_for_element = False
                            break
                    break

                # If the fetchstream list is empty, try the u_0_ element name
                if not fetchstream_list:

                    # List containing all 'u_0_ ...' element names
                    u_0_list = []

                    # Find all the 'u_0_' elements on page
                    for elements in soup.findAll('div', id=re.compile("u_0_")):
                        u_0_list.append(elements['id'])

                    # Loop through the u_0_list, creat the xpath and try
                    # clicking the element.
                    search_for_element = True
                    while search_for_element:
                        for xpath in u_0_list:
                            element = "//*[@id='" + xpath + "']/li[3]/a"
                            try:
                                driver.find_element_by_xpath(element).click()
                            except NoSuchElementException:
                                pass
                            else:
                                search_for_element = False
                                break
                        break

                # Call the friends loop function
                friends_loop()

            def friends_loop():

                """ Selenium WebDriver will find the friends search box
                and type either:
                * 192 other occupants
                * Known friend

                """

                def find_textbox():

                    """ Selenium WebDriver will find the friends search
                    box element.

                    """

                    # Delay BeautifulSoup getting the page source
                    time.sleep(Config.sleep)

                    # Tell BeautifulSoup to get the page source
                    html = driver.page_source
                    soup = BeautifulSoup(html, "lxml")

                    # List containing all the 'fetchstream' element names
                    fetchstream_list = []

                    # Declare bool to state friends search box is not visible
                    # meaning the profie privacy does not allow you to search 
                    failed_to_find = True

                    # Find all the 'fetchstream' element names and add to
                    # the fetchstream_list.
                    for elements in soup.findAll('span', id=re.compile
                                                 ("u_fetchstream_")):
                        fetchstream_list.append(elements['id'])

                    # Loop through the fetchstream_list and create the
                    # xpath and try clicking the element.
                    search_for_element = True
                    while search_for_element:
                        for element in fetchstream_list:
                            xpath = "//*[@id='" + element + "']/span/input"

                            try:
                                searchbox = driver.find_element_by_xpath(xpath)

                            except NoSuchElementException:
                                if fetchstream_list[len(fetchstream_list)-1]:
                                    failed_to_find = True
                                else:
                                    pass
                            else:
                                # End the while loop
                                search_for_element = False

                                # Declare the friends search box visible
                                failed_to_find = False
                                break

                        break

                    time.sleep(Config.sleep)
                    # Check if profile privacy settings don't allow
                    # the friends list to be searched.
                    if failed_to_find is True:

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " This persons privacy settings" +
                                             " do not allow you to see their" +
                                             " friends list." +
                                             " Closing browser.\n")

                        # Go back 2 pages and call the profile_loop function to
                        # check another profile.
                        driver.execute_script("window.history.go(-2)")

                        # Call the profile_loop function
                        profile_loop()

                    else:
                        return searchbox

                # Wait for element to appear on page - preventing Strelok
                # from prematurely going back.
                time.sleep(Config.sleep + 1.0)

                # Call the find_textbox() function and return the element
                # name (search element)
                searchbox = find_textbox()

                # Variable used if the profile is a match
                Search.profile_name = driver.title

                # Do this if the Known Friend textbox in Strelok has text
                if known_friend != "":
                    output_buffer.insert(output_iter,
                                         time.strftime("%H:%M:%S") +
                                         " Entering " +
                                         known_friend.title() +
                                         " into the search friend" +
                                         " entry box\n")

                    # Enter the known friend into the friends search box
                    searchbox.send_keys(known_friend.title())
                    searchbox.send_keys(Keys.RETURN)

                    # Wait and then get the page source using BeautifulSoup
                    time.sleep(Config.sleep)
                    html = driver.page_source
                    soup = BeautifulSoup(html, "lxml")

                    if soup.find_all("div", text="Results for: " +
                                     known_friend.title()):

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Known friend has been found\n")

                        # Add profile to results table
                        fb_contents = [("Profile for " +
                                        Search.profile_name,
                                        "Facebook",
                                        Search.facebook_profile_url)]

                        for item in fb_contents:
                            Results.liststore.append(list(item))

                        # Call the scrape function
                        scrape()

                    else:
                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Known friend has not been" +
                                             " found\n")

                        # Go back 2 pages in the browser
                        driver.execute_script("window.history.go(-2)")

                        # Call the profile_loop function
                        profile_loop()

                # Do this if the Known Friend textbox is empty
                elif known_friend == "":
                    for name in Search.occupants_list:

                        # Convert list item to string (First Name Last Name)
                        occupant = ' '.join(name)

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Entering " + occupant +
                                             " into the Search Friends" +
                                             " text box\n")

                        # Enter name into search box
                        searchbox.send_keys(occupant)
                        searchbox.send_keys(Keys.RETURN)

                        # Delay due to BeautifulSoup getting the page
                        # source before the page has loaded.
                        time.sleep(Config.sleep + 1.5)

                        # BeautifulSoup - get page source
                        html = driver.page_source
                        soup = BeautifulSoup(html, "lxml")

                        # Check if the 192 occupant has not been found
                        if soup.find_all("div", text="No results for: " +
                                         occupant):

                            output_buffer.insert(output_iter,
                                                 time.strftime("%H:%M:%S") +
                                                 " " + occupant +
                                                 " has not been found\n")

                            # Clear the search box
                            searchbox.clear()

                            # Clear the string ready to be used again.
                            # Otherwise it will just add the next name
                            # from list
                            occupant = ""

                            # Prepare for when 192 occupants list is at
                            # the end to initiate the process of going to
                            # and checking another profiles' friends list
                            end_of_list = True

                        # If 192 occupant is found on the Facebook profiles
                        # friends list
                        else:
                            output_buffer.insert(output_iter,
                                                 time.strftime("%H:%M:%S") +
                                                 " " + occupant +
                                                 " has been found\n")

                            # Add profile to Results pane.
                            fb_contents = [(target_name.title(),
                                            "Facebook",
                                            Search.facebook_profile_url)]

                            for item in fb_contents:
                                Results.liststore.append(list(item))

                            # State that a profile has been found, no need
                            # to go to another profile.
                            end_of_list = False

                            # Call the scrape function
                            scrape()

                    # Check if occupants_list is at the end and then switch
                    # profiles
                    if end_of_list is True:
                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " No searched for friends" +
                                             " have been found on" +
                                             " profile, checking another\n")

                        # Tell Selenium WebDriver go go back 2 pages
                        driver.execute_script("window.history.go(-2)")

                        # Re-call the profile_loop function to restart the
                        # process of finding 192 occupants in profiles
                        profile_loop()

            def scrape():

                """ Selenium WebDriver will go to the About Page
                to scrape work and education data.

                """

                output_buffer.insert(output_iter,
                                     time.strftime("%H:%M:%S") +
                                     " Scraping " +
                                     target_name.title() +
                                     "s' profile\n")

                # Get the LinkedIn checkbox from the Glade XML
                linkedin_check = builder.get_object("linkedin_check")

                Search.iterating_profiles = False

                def about_button():

                    """ Selenium WebDriver will click
                    the About button, on Facebook.

                    """

                    # Delay BeautifulSoup getting the page source
                    time.sleep(Config.sleep)

                    # Tell BeautifulSoup to get the page source
                    html = driver.page_source
                    soup = BeautifulSoup(html, "lxml")

                    # List containing all the 'fetchstream' element names
                    fetchstream_list = []

                    # Find all the 'fetchstream' element names and add to
                    # the fetchstream_list.
                    for elements in soup.findAll('ul', id=re.compile
                                                 ("u_fetchstream_")):
                        fetchstream_list.append(elements['id'])

                    # Loop through the fetchstream_list and create the
                    # xpath and try clicking the element.
                    search_for_element = True
                    while search_for_element:
                        for element in fetchstream_list:
                            xpath = "//*[@id='" + element + "']/li[2]/a"

                            try:
                                driver.find_element_by_xpath(xpath).click()
                            except NoSuchElementException:
                                pass
                            else:
                                search_for_element = False
                                break
                        break

                    # If the fetchstream list is empty, try the u_0_
                    # element name
                    if not fetchstream_list:

                        # List containing all 'u_0_ ...' element names
                        u_0_list = []

                        # Find all the 'u_0_' elements on page
                        for elements in soup.findAll('ul', id=re.compile
                                                     ("u_0_")):
                            u_0_list.append(elements['id'])

                        # Loop through the u_0_list, creat the xpath and
                        # try clicking the element.
                        search_for_element = True
                        while search_for_element:
                            for element in u_0_list:
                                xpath = "//*[@id='" + element + "']/li[2]/a"

                                try:
                                    driver.find_element_by_xpath(xpath).click()
                                except NoSuchElementException:
                                    pass
                                else:
                                    search_for_element = False
                                    break
                            break

                def contact_button():

                    """ Selenium WebDriver will click the
                    Contact and Basic Info button, on Facebook.

                    """

                    # Delay BeautifulSoup getting the page source
                    time.sleep(Config.sleep)

                    # Tell BeautifulSoup to get the page source
                    html = driver.page_source
                    soup = BeautifulSoup(html, "lxml")

                    # List containing all the 'fetchstream' element names
                    fetchstream_list = []

                    # Find all the 'fetchstream' element names and add to
                    # the fetchstream_list.
                    for elements in soup.findAll('div', id=re.compile
                                                 ("u_fetchstream_")):
                        fetchstream_list.append(elements['id'])

                    # Loop through the fetchstream_list and create the
                    # xpath and try clicking the element.
                    search_for_element = True
                    while search_for_element:
                        for element in fetchstream_list:
                            xpath = "//*[@id='" + element + "']/div/ul/li[4]/a"

                            try:
                                driver.find_element_by_xpath(xpath).click()
                            except NoSuchElementException:
                                pass
                            else:
                                search_for_element = False
                                break
                        break

                    # If the fetchstream list is empty, try the u_0_
                    # element name
                    if not fetchstream_list:

                        # List containing all 'u_0_ ...' element names
                        u_0_list = []

                        # Find all the 'u_0_' elements on page
                        for elements in soup.findAll('div', id=re.compile
                                                     ("u_0_")):
                            u_0_list.append(elements['id'])

                        # Loop through the u_0_list, creat the xpath and
                        # try clicking the element.
                        search_for_element = True
                        while search_for_element:
                            for element in u_0_list:
                                xpath = ("//*[@id='" + element +
                                         "']/div/ul/li[4]/a")
                                try:
                                    driver.find_element_by_xpath(xpath).click()
                                except NoSuchElementException:
                                    pass
                                else:
                                    search_for_element = False
                                    break
                            break

                    # If Contact and Basic Info button still hasn't been
                    # clicked - try use the css_selector
                    driver.find_element_by_css_selector(
                        "[data-testid='nav_contact_basic']").click()

                def work_button():

                    """ Selenium WebDriver will click the
                    Work and Education button, on Facebook.

                    """

                    # Delay BeautifulSoup getting the page source
                    time.sleep(Config.sleep)

                    # Tell BeautifulSoup to get the page source
                    html = driver.page_source
                    soup = BeautifulSoup(html, "lxml")

                    # List containing all the 'fetchstream' element names
                    fetchstream_list = []

                    # Find all the 'fetchstream' element names and add to
                    # the fetchstream_list.
                    for elements in soup.findAll('div', id=re.compile
                                                 ("u_fetchstream_")):
                        fetchstream_list.append(elements['id'])

                    # Loop through the fetchstream_list and create the
                    # xpath and try clicking the element.
                    search_for_element = True
                    while search_for_element:
                        for element in fetchstream_list:
                            xpath = ("//*[@id='" + element +
                                     "']/div/ul/li[2]/a")

                            try:
                                driver.find_element_by_xpath(xpath).click()
                            except NoSuchElementException:
                                pass
                            else:
                                search_for_element = False
                                break
                        break

                    # If the fetchstream list is empty, try the u_0_
                    # element name
                    if not fetchstream_list:

                        # List containing all 'u_0_ ...' element names
                        u_0_list = []

                        # Find all the 'u_0_' elements on page
                        for elements in soup.findAll('div', id=re.compile
                                                     ("u_0_")):
                            u_0_list.append(elements['id'])

                        # Loop through the u_0_list, create the xpath and
                        # try clicking the element.
                        search_for_element = True
                        while search_for_element:
                            for element in u_0_list:
                                xpath = ("//*[@id='" + element +
                                         "']/div/ul/li[2]/a")

                                try:
                                    driver.find_element_by_xpath(xpath).click()
                                except NoSuchElementException:
                                    pass
                                else:
                                    search_for_element = False
                                    break
                            break

                    # If Work and Education button still hasn't been
                    # clicked - try use the css_selector
                    driver.find_element_by_css_selector(
                        "[data-testid='nav_edu_work']").click()

                # Call the about_button function to click the About button
                # on Facebook
                about_button()

                # Call the contact_button to click the Contact button on
                # Facebooks' About page
                contact_button()

                # Call the work_button to click the Work and Education
                # button from Facebooks About/Contact page
                work_button()

                # Delay BeautifulSoup --> then gather the page source
                time.sleep(Config.sleep)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # This is here because it works, can't replace with
                # normal soup, needs prettify.
                profile_soup = soup.prettify()

                # Get the Facebook profiles' ID
                Search.profile_id = re.search(r"profile_id=[0-9]+",
                                              profile_soup)
                Search.profile_id = re.search(r"[0-9]+",
                                              Search.profile_id.group()).group() if Search.profile_id else 'permission denied'

                # It's more efficient to thread this function, as
                # Selenium is needed elsewhere.
                thread = Thread(target=profile_data)
                thread.start()

                # Scrape Work and Education provided either a education
                # or work is found on the profile.
                if soup.find_all('span', text="No workplaces to show") and soup.find_all('span', text="No schools to show"):
                    output_buffer.insert(output_iter,
                                         time.strftime("%H:%M:%S") +
                                         " " + target_name.title() +
                                         "'s profile does not have" +
                                         " a work or education list," +
                                         " cannot continue.\n")
                    driver.close()
                    return

                else:
                    output_buffer.insert(output_iter,
                                         time.strftime("%H:%M:%S") +
                                         " Scraping " + target_name.title() +
                                         "'s work or education.\n")

                    for info in soup.find_all('div',
                                              attrs={"class":
                                                     "_2lzr _50f5 _50f7"}):
                        info_string = info.get_text()

                        # Remove text between brackets e.g. (UCLan)
                        info_string = re.sub(r"[\(\[].*?[\)\]]",
                                             "", info_string)

                        # Remove the trailing white space
                        info_string = re.sub(r'\s+$', '', info_string)

                        # Add to Search/profile_info list
                        Search.profile_info.append(info_string)

                    # Convert profile_info list to a string and add
                    # to the SCRAPE DATA textbox
                    scrape_list = '\n'.join(Search.profile_info)
                    scrape_buffer.insert(scrape_iter, scrape_list)

                    if linkedin_check.get_active():
                        driver.close()
                        search_linkedin()
                    else:
                        progress_bar = builder.get_object("progress_bar")
                        progress_bar.set_text("Finished!")
                        progress_bar.set_pulse_step(0.00)
                        driver.close()
                        return

            def profile_data():

                """ Use Facebooks Graph search to find information on a
                profile. This includes:
                * Photos
                * Videos
                * Posts
                * Groups
                * Places
                * Events
                * Friends

                """

                # The 3rd part of Facebook's Graph search URLs.
                facebook_link = ["/photos-of", "/photos-by", "/photos-liked",
                                 "/photos-commented", "/videos-by",
                                 "/videos-liked", "/videos-commented",
                                 "/stories-tagged", "/groups",
                                 "/stories-liked", "/places-liked/",
                                 "/places-visited/", "/places-checked-in/",
                                 "/events", "/friends", "/friends/friends"]

                # List of the "Page Titles" that are to be displayed in
                # the Results table.
                page_name = ["Photos of ", "Photos by ", "Photos liked by ",
                             "Photos commented on by ", "Videos by ",
                             "Videos liked by ", "Videos commented on by ",
                             "Posts about ", "Groups with ", "Posts liked by ",
                             "Places liked by ", "Places visited by ",
                             "Places checked in at by ", "Events with ",
                             "Friends of ", "Friends of friends of "]

                # No need for Selenium here, the URLs can be hardcoded.
                for link, page in zip(facebook_link, page_name):

                    # Format the URL by adding the constant HTTPS link
                    # and the profile name/target name + the facebook_links
                    # list above
                    url = ("https://www.facebook.com/search/" +
                           Search.profile_id + link)

                    # Format the page name by adding the an item from the
                    # page_names list to the profile name/target name
                    page_url = page + Search.profile_name

                    # Add the page name, the website (Facebook) and the
                    # URL and append the Results table.
                    results = [page_url, "Facebook", url]
                    Results.liststore.append(results)

            # Call the search_bar function to start the initial search
            search_bar()

        def search_linkedin():

            """ Selenium WebDriver searches LinkedIn using the data
            scraped from the Facebook profile.

            """

            output_buffer.insert(output_iter,
                                 time.strftime("%H:%M:%S") +
                                 " Starting the search for " +
                                 target_name.title() +
                                 " from " +
                                 target_loc.title() +
                                 " on LinkedIn.com \n")

            # Set Chrome options to hide the browser window
            CHROME_PATH = '/usr/bin/google-chrome'
            CHROMEDRIVER_PATH = '/usr/bin/chromedriver'
            #WINDOW_SIZE = "1920,1080"

            chrome_options = Options()
            #chrome_options.add_argument("--headless")
            #chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
            chrome_options.binary_location = CHROME_PATH

            driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                                      chrome_options=chrome_options
                                     )

            # Go to LinkedIn.com using Selenium WebDriver
            driver.get(Search.websites[2])

            # If cookies exist, add to Selenium WebDriver and refresh the page
            if os.stat('linkedin_cookies').st_size != 0:
                output_buffer.insert(output_iter,
                                     time.strftime("%H:%M:%S") +
                                     " LinkedIn cookies have" +
                                     " been found, adding to" +
                                     " browser\n")

                with open('linkedin_cookies', 'rb') as cookiefile:
                    cookies = pickle.load(cookiefile)
                    for cookie in cookies:
                        driver.add_cookie(cookie)

                driver.refresh()

            # If no cookies exist, log in as normal
            elif os.stat('linkedin_cookies').st_size == 0:
                output_buffer.insert(output_iter,
                                     time.strftime("%H:%M:%S") +
                                     " No Linkedin cookies have been found\n")

                output_buffer.insert(output_iter,
                                     time.strftime("%H:%M:%S") +
                                     " Entering LinkedIn username and" +
                                     " password\n")

                login_element = driver.find_element_by_id("login-email")
                login_element.send_keys(Config.linkedin_username)
                login_element = driver.find_element_by_id("login-password")
                login_element.send_keys(Config.linkedin_password)

                time.sleep(Config.sleep)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")
                

                output_buffer.insert(output_iter,
                                    time.strftime("%H:%M:%S") +
                                    " Logging into LinkedIn\n")

                login_element.send_keys(Keys.RETURN)

                # Add cookies to linkedin_cookies file.
                with open('linkedin_cookies', 'wb') as filehandler:
                    pickle.dump(driver.get_cookies(), filehandler)

                output_buffer.insert(output_iter,
                                    time.strftime("%H:%M:%S") +
                                    " Dumping LinkedIn cookies" +
                                    " into linkedin_cookies\n")

            def search_bar():

                """ Selenium WebDriver will find the search bar
                and enter the "targets name and location"

                """

                #print ("search bar reached")

                # Delay BeautifulSoup from getting the page source
                time.sleep(Config.sleep + 0.5)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                #print (html)

                # List containing the search result pages 'ember'
                # elements
                ember_list = []

                # Find all 'a' elements with the id 'ember' and
                # add the ID to a list
                for elements in soup.findAll('artdeco-typeahead-deprecated-input',
                                             id=re.compile("ember")):
                    ember_list.append(elements['id'])

                searchbox_found = False
                
                #print (ember_list)

                # Find search bar element on LinkedIn page by looping
                # through list of elements
                for element in ember_list:
                    xpath = "//*[@id='" + element + "']/input"
                    #print ("test")
                    try:
                        search_element = driver.find_element_by_xpath(xpath)
                    except NoSuchElementException:
                        pass
                    else:
                        searchbox_found = True
                        break

                # Check if ember_list is empty
                if not ember_list:
                    try:
                        search_element = driver.find_element_by_xpath(
                            "//*[@id='mount']/div/div/nav/" +
                            "div[2]/form/div/input")
                    except NoSuchElementException:
                        pass
                    else:
                        searchbox_found = True

                if searchbox_found:
                    # Send targets name + location to the search bar textbox.
                    search_element.send_keys(target)
                    search_element.send_keys(Keys.RETURN)
                    time.sleep(0.5)

                    # Call the 'people_button' function when search bar is
                    # found.
                    people_button()

            def people_button():

                """ Selenium WebDriver will click the People
                button.

                """

                # BeautifulSoup will get the page source
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # List containing the search result pages 'ember' elements
                ember_list = []

                # Find all 'a' elements with the id 'ember' and add the ID
                # to a list
                for elements in soup.findAll('div', id=re.compile("ember")):
                    ember_list.append(elements['id'])

                for element in ember_list:
                    xpath = "//*[@id='" + element + "']/ul/li[1]/button"
                    try:
                        driver.find_element_by_xpath(xpath).click()
                    except NoSuchElementException:
                        pass
                    else:
                        break

                # Call the check_results function
                check_results()

            def check_results():

                """ BeautifulSoup will scrape the number of search results
                found.

                """

                # Delay BeautifulSoup from getting the page source
                time.sleep(Config.sleep)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # Check if there are any results on the page
                if soup.find_all("div", {"class":
                                         "search-no-results__container"}):

                    output_buffer.insert(output_iter,
                                         time.strftime("%H:%M:%S") +
                                         " No results found on" +
                                         " LinkedIn, closing" +
                                         " the browser\n")

                    # If no results found, close the browser
                    driver.close()
                    return

                # When results have been found
                else:
                    results = soup.find('h3', {"class": re.compile
                                               ("search-results__total")})

                    # Extract text between elements and add to variable
                    results = results.string

                    # Strip string and extract number of results found only.
                    self.result = [int(s) for s in results.split() if s.isdigit()]

                    # Call the profile_loop function
                    profile_loop()

            def profile_loop():

                """ Selenium WebDriver will loop through the profiles
                found and compare to data scraped from Facebook with
                the data on the LinkedIn profiles.

                """

                # Delay BeautifulSoup from getting th page source
                time.sleep(Config.sleep + 1.0)
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # List containing the search result pages 'ember' elements
                ember_list = []

                # Find all 'h3' elements with the ID 'ember' and add the ID
                # to a list
                for elements in soup.findAll('a', id=re.compile("ember")):
                    ember_list.append(elements['id'])

                # Find "/premium/products/" links using regex and add them
                # to the ignore list
                # This link changes occassionally on page refresh.
                for href in soup.findAll('a', href=re.compile
                                         ("/premium/products/")):
                    Search.ignore_list.append(href['href'])

                # Loop through ember_list
                for ember in ember_list:

                    # Find 'a' elements with the ember_list list item 'id'
                    for href in soup.findAll('a', id=ember):

                        # Check if the 'href' is in the ignore list
                        if href['href'] in Search.ignore_list:
                            pass
                        else:
                            # Create the complete xpath using item from
                            # ember_list
                            profile_xpath = "//*[@id='" + ember + "']"

                            # Check if the xpath exists and click it.
                            try:
                                driver.find_element_by_xpath(profile_xpath).click()
                            except NoSuchElementException:
                                pass
                            except ElementNotVisibleException:
                                pass
                            else:
                                # Add href to ignore list so it won't be
                                # clicked in the future.
                                Search.ignore_list.append(href['href'])

                                # Call the check_profile function
                                check_profile()

            def check_profile():

                """ BeautifulSoup will compare the data scraped from
                Facebook with the data from on the LinkedIn profile.

                """

                # The number of data found on the LinkedIn profile -
                # to check the accuracy of profile_list results.
                accuracy_counter = 0

                # Delay BeautifulSoup getting the page source too
                # quickly
                time.sleep(Config.sleep + 1.0)

                # Get the HTML page source.
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")

                # Loop through profile_info list (gathered from Facebook)
                # and check if the text exists on the LinkedIn page
                for item in Search.profile_info:

                    if soup.find_all('h3', text=item):

                        # If data if found on the Linkedin profile, add
                        # to the accuracy counter
                        accuracy_counter += 1
                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             item + " Has been found" +
                                             " on this profile\n")

                    else:
                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             item + " Has not been found" +
                                             " on this profile\n")

                # If the accuracy counter is above 1 (indicating data
                # is found), add profile to Results table and close
                # the browser.
                if accuracy_counter >= 1:

                    # Add URL to Results table
                    linkdin_url = driver.current_url
                    linkedin_contents = [(target_name.title(),
                                         "LinkedIn", linkdin_url)]
                    for item in linkedin_contents:
                        Results.liststore.append(list(item))

                    # Close the browser after the profile has been found
                    driver.close()

                else:
                    if self.result == 1:

                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             " Only one profile has been" +
                                             " found, this has been added" +
                                             " to the results table\n")

                        # Add URL to Results table
                        linkdin_url = driver.current_url
                        linkedin_contents = [(target_name.title(),
                                              "[POTENTIAL] LinkedIn",
                                              linkdin_url)]

                        for item in linkedin_contents:
                            Results.liststore.append(list(item))

                    else:
                        output_buffer.insert(output_iter,
                                             time.strftime("%H:%M:%S") +
                                             "No match, trying another" +
                                             "profile")
                        # Go back a page
                        driver.execute_script("window.history.go(-1)")

                        # Call the profile_loop function to go to another
                        # profile
                        profile_loop()

                progress_bar = builder.get_object("progress_bar")
                progress_bar.set_text("Finished!")
                progress_bar.set_pulse_step(0.00)

            # Start the initial LinkedIn search
            search_bar()

        def progress_bar():

            """ A threaded progress bar to indicate
            a search is underway.

            """
            
            progress_bar = builder.get_object("progress_bar")
            progress_bar.set_text("Search In Progress...")
            progress_bar.pulse()

        if target_name == "" or target_loc == "":
            search_error()

        elif target_name != "" and target_loc != "":

            if Config.facebook_username == "" or Config.facebook_password == "":
                facebook_error()

            elif Config.facebook_username != "" and Config.facebook_password != "":

                notebook = builder.get_object("notebook")
                notebook.set_current_page(1)
                output_buffer.set_text("")  # clear logbox

                if known_friend != "":

                    # Start the progress bar thread
                    progress_thread = Thread(target=progress_bar, name="Progress Thread")
                    progress_thread.start()
                    Search.progress_bar = True

                    # Start the Facebook search thread
                    thread = Thread(target=search_facebook, name="Facebook Thread")
                    thread.start()

                elif known_friend == "":

                    # Start the progress bar thread
                    progress_thread = Thread(target=progress_bar, name="Progress Thread")
                    progress_thread.start()
                    Search.progress_bar = True

                    # Start the 192 search thread
                    thread = Thread(target=search_192, name="192 Thread")
                    thread.start()

        else:
            facebook_error()


def main():

    """ Keep the main window open

    """

    Gtk.main()
    return 0

if __name__ == "__main__":

    """ Includes the XML Handlers.

    """

    def about_dialog(*args):

        """ Opens the About dialog when the button
        is clicked in the menu bar.

        """

        dialog = builder.get_object("about_dialog")
        dialog.run()
        dialog.hide()

    def user_manual(*args):

        """ Takes the user to the GitHub URL
        page when the User Manual button is
        clicked in the menu bar.

        """

        webbrowser.open('https://github.com/dkspencer/strelok/', new=2)

    def exit_dialog(*args):

        """ Shows the exit dialog window when
        the Exit button is clicked in the menu bar.

        """

        dialog = builder.get_object("exit_dialog")
        dialog.show_all()

    def exit_dialog_yes(*args):

        """ Deletes the contents of the cookies
        files on exit - prevents the cookies from
        expiring.
        User can use the x button top-left to close
        without deleting the cookies.

        """

        open('facebook_cookies', 'w').close()
        open('linkedin_cookies', 'w').close()
        Gtk.main_quit()

    def exit_dialog_no(*args):

        """ Closes the dialog window and does not
        exit the program.

        """

        dialog = builder.get_object("exit_dialog")
        dialog.hide()

    def facebook_error_back(*args):

        """ Closes the Facebook error dialog - the
        dialog where no username or password
        is entered for Facebook.

        """

        error = builder.get_object("facebook_error")
        error.hide()

    def search_error_close(*args):

        """ Closes the name and location error dialog
         - happens when no target name or location is
         entered into the program.

        """

        search_error = builder.get_object("search_error")
        search_error.hide()

    def search_error(*args):

        """ Displays the search error dialog box
         - happens when no target name or location is
         entered.

        """

        dialog = builder.get_object("search_error")
        dialog.show_all()

    def facebook_error():

        """ Displays the Facebook error dialog when
        no Facebook username or password is entered
        into the program.

        """

        dialog = builder.get_object("facebook_error")
        dialog.show_all()

    def invalid_facebook():

        """ Displays the Facebook username or password
        error when invalid credentials are used to log
        into Facebook.

        """

        dialog = builder.get_object("invalid_fb_dialog")
        dialog.show_all()

    def invalid_facebook_back(self):

        """ Hides the invalid Facebook login details
        dialog.

        """

        dialog = builder.get_object("invalid_fb_dialog")
        dialog.hide()

    def invalid_linkedin_back(self):

        """ Hides the invalid LinkedIn login details
        dialog.

        """

        dialog = builder.get_object("invalid_lnkdn_dialog")
        dialog.hide()

    def facebook_results_ok():

        """ Hides the Facebook results error dialog box
        that appears when the Facebook profile cannot be
        found.

        """

        dialog = builder.get_object("facebook_results_error")
        dialog.hide()

    def linkedin_results_ok():

        """ Hides the LinkedIn results error dialob box that
        appears when the LinkedIn profile cannot be found.

        """

        dialog = builder.get_object("linkedin_results_error")
        dialog.hide()

    def results_dialog_192():

        """ Displays the 192 error dialog when
        no names can be found on the website.

        """

        dialog = builder.get_object("192_results_dialog")
        dialog.show_all()

    def results_dialog_192_ok():

        """ Hides the 192 error dialog when
        no names can be found on the website.

        """

        dialog = builder.get_object("192_results_dialog")
        dialog.hide()
    
    def results_dialog_facebook():

        """ Displays the Facebook error dialog when
        no names can be found on the website.

        """

        dialog = builder.get_object("facebook_results_dialog")
        dialog.show_all()

    def results_dialog_facebook_ok():

        """ Hides the Facebook error dialog when
        no names can be found on the website.

        """

        dialog = builder.get_object("facebook_results_dialog")
        dialog.hide()

    def results_dialog_linkedin():

        """ Displays the LinkedIn error dialog when
        no names can be found on the website.

        """

        dialog = builder.get_object("linkedin_results_dialog")
        dialog.show_all()

    def results_dialog_linkedin_ok():

        """ Hides the LinkedIn error dialog when
        no names can be found on the website.

        """

        dialog = builder.get_object("linkedin_results_dialog")
        dialog.hide()

    # Ties the GLADE GTK XML objects to code functions.
    handler = {
               "verify_button": EULA_Assistant.verify_button,
               "about_dialog": about_dialog,
               "file_exit": exit_dialog,
               "filter_save": Config.save_changes,
               "filter_close": Config.revert_changes,
               "content_clear": Results.clear_button,
               "user_manual": user_manual,
               "open_link": Results.open_link_button,
               "delete_link": Results.delete_link_button,
               "search_clear": Search.clear_button,
               "search_error_close": search_error_close,
               "search": Search.search_button,
               "exit_dialog_yes": exit_dialog_yes,
               "exit_dialog_no": exit_dialog_no,
               "facebook_back": facebook_error_back,
               "invalid_facebook_back": invalid_facebook_back,
               "invalid_linkedin_back": invalid_linkedin_back,
               "fb_error_back": facebook_results_ok,
               "lnkdn_error_back": linkedin_results_ok,
               }

    # The output buffer is the logbox at the bottom of the window.
    # Displays all the critical information and gives the user
    # feedback
    output_buffer = builder.get_object("output_buffer")
    output_iter = output_buffer.get_end_iter()

    # The scrape_buffer is the textview box under SCRAPED DATA in
    # the bottom right-hand corner.
    # Contains all the scraped data from Facebook
    scrape_buffer = builder.get_object("scrape_buffer")
    scrape_iter = scrape_buffer.get_end_iter()

    # Closes Strelok (the window)
    application_window.connect("delete-event", Gtk.main_quit)

    # Connects the Glade/XML object names to functions in the code
    builder.connect_signals(handler)

    # Displays the GTK window on screen.
    application_window.show_all()

    # Invoke the main function
    main()
