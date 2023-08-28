import time

from selenium import webdriver
from selenium.webdriver.common.by import By
import os
import base64


def main():
    driver = webdriver.Chrome()
    driver.get("https://app.crowdmark.com/sign-in/waterloo")

    input("Press Enter after logging in: ")

    assert "Crowdmark" in driver.title
    working_directory = os.getcwd()

    output_directory = os.path.join(working_directory, "output")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    start_time = time.time()
    download_assessments_for_ith_page(driver, output_directory, 1)
    end_time = time.time()

    elapsed_time = end_time - start_time
    print("Finished downloading in: ", elapsed_time, " seconds!")
    driver.close()
    exit(0)


def download_assessments_for_ith_page(driver, output_directory, starting_page):
    page_num = starting_page
    # for each page in crowdmark, install each assessment
    while True:
        # driver.get(f"https://app.crowdmark.com/student/courses?page={page_num}")
        driver.get(f"https://app.crowdmark.com/student/course-archive?page={page_num}")
        time.sleep(3)  # wait for page to load. For some reason driver.get doesn't wait for the entire page to load

        course_list = driver.find_element(By.CLASS_NAME, "student-dashboard__course-list")

        a_tags = course_list.find_elements(By.TAG_NAME, "a")

        if len(a_tags) == 0:
            # there are no more links on this page, so we have scraped all the assessments
            return

        urls = [a_tag.get_attribute("href") for a_tag in a_tags]
        for url in urls:
            download_assessments_for_course(driver, output_directory, url)

        page_num += 1


def download_assessments_for_course(driver, output_directory, url):
    course_name = page_name(url)
    driver.get(url)
    time.sleep(3)  # wait for page to load. For some reason driver.get doesn't wait for the entire page to load

    course_output_directory = os.path.join(output_directory, course_name)
    if not os.path.exists(course_output_directory):
        os.makedirs(course_output_directory)

    a_tags = driver.find_elements(By.TAG_NAME, "a")
    urls = [a_tag.get_attribute("href") for a_tag in a_tags]
    for assessment_url in urls:
        if (not assessment_url) or ("assessments" not in assessment_url):
            # this link doesn't take you to an assessment
            continue
        download_assessment(driver, course_output_directory, assessment_url)


def download_assessment(driver, course_output_directory, url):
    driver.get(url)
    time.sleep(5)  # wait for page to load. For some reason driver.get doesn't wait for the entire page to load
    assessment_name = page_name(url)
    html = driver.page_source

    assessment_output_directory = os.path.join(course_output_directory, assessment_name)
    if not os.path.exists(assessment_output_directory):
        os.makedirs(assessment_output_directory)

    with open(f"{assessment_output_directory}/index.html", "w", encoding="utf-8") as file:
        file.write(html)
    buttons = driver.find_elements(By.CSS_SELECTOR, "ul button")
    if len(buttons) == 0:
        return
    for button in buttons:
        button.click()
        time.sleep(1)
        canvas_file_name = f"{assessment_output_directory}/{button.get_attribute('innerHTML')}.png"
        # https://stackoverflow.com/questions/44485616/web-scraping-image-inside-canvas
        # get the base64 representation of the canvas image (the part substring(21) is for removing the padding "data:image/png;base64")
        # canvas = driver.find_elements(By.TAG_NAME, "canvas");
        canvas = driver.find_elements(By.CSS_SELECTOR, ".score-distribution__chart");
        if len(canvas) != 1:
            print("wut")
            print(canvas)
            continue
        canvas = canvas[0]
        canvas_png = canvas.screenshot_as_png
        # canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", canvas)
        # canvas_png = base64.b64decode(canvas_base64)
        with open(canvas_file_name, "wb") as graph:
            graph.write(canvas_png)




def page_name(url):
    return url.rsplit('/', 1)[-1]


if __name__ == '__main__':
    main()
