from tkinter import *
from tkinter import filedialog, messagebox
import os
import subprocess
import selenium
from selenium import webdriver
import time

root = Tk()
root.withdraw()

def get_length(filename):
    result = subprocess.run(["C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe", "-v", "error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)


def download_gpx():
	print("Configuring Chrome")
	options = webdriver.ChromeOptions()
	options.add_argument("--headless")
	options.add_argument("--disable-gpu")
	options.add_experimental_option("prefs", {
	  "download.default_directory": path + "\\output\\",
	  "download.prompt_for_download": False,
	  "download.directory_upgrade": True,
	  "safebrowsing.enabled": True
	})
	print("Launching Chrome")
	driver = webdriver.Chrome(options=options, executable_path='C:/Program Files (x86)/chromedriver/chromedriver.exe')
	print("Bypassing checks")
	driver.get('https://goprotelemetryextractor.com/free/')

	driver.find_element_by_css_selector("button[class='btn btn-outline-primary btn-sm hideVersionPicker']").click()
	driver.find_element_by_name('email').send_keys('testing@gmail.com')

	driver.find_element_by_css_selector("input[type='submit']").click()
	print("Uploading file")
	driver.find_element_by_css_selector("input[type='file']").send_keys(output_merged_file)
	print("Waiting for file to upload")
	progress_bar = driver.find_element_by_css_selector("div[class='progress-bar progress-bar-striped progress-bar-animated bg-info']")
	while progress_bar.get_attribute("aria-valuenow") != "100":
		pass
	print("File uploaded")
	def try_type_element():
		try:
			driver.find_element_by_css_selector("button[class='btn btn-outline-primary btn-sm btn-block mt-0 mb-1 gpmf-stream']").click()
		except:
			time.sleep(1)
			try_type_element()
	print("Waiting for webpage to update")
	try_type_element()

	driver.find_element_by_css_selector("button[gpmf-key='gpx'][data-original-title='GPS Exchange Format is compatible with many apps']").click()
	print("Downloading GPX data")
	loop_until_file_downloaded()
	driver.quit()

def loop_until_file_downloaded():
	try:
		gpx_file = [f for f in os.listdir(path + "\\output") if os.path.isfile(os.path.join(path + "\\output", f)) if f.endswith(".gpx")][0]
		print("Downloaded GPX data")
		os.rename(path + "\\output\\" + gpx_file, path + "\\output\\merged.gpx")
		print("Renamed GPX file")
	except:
		time.sleep(1)
		loop_until_file_downloaded()

def sort_files(path):
	print("Renaming files")
	files_to_sort = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) if f.startswith("GX")]

	new_list = [(file[6:8], file) for file in files_to_sort]

	x = sorted(new_list, key=lambda x: x[0])

	y = [z[1] for z in x]

	for pos, file in enumerate(y):
		print(str(file) + " -> " + str(pos))
		os.rename(os.path.join(path, file), os.path.join(path, str(pos)+".mp4"))

	print("Renamed files")

user_input = messagebox.askquestion("Yes/No", "Speed up file after merging?", icon='info')
print(f"Selected {user_input}")
if user_input.lower() == "yes":
	speed_up = True
else:
	speed_up = False

path = filedialog.askdirectory().replace("/", "\\")
sort_files(path)

print("Checking file paths")
if not os.path.exists(path + "\\output"):
	os.mkdir(path + "\\output")
input_file = path + "\\input.txt"
output_merged_file = path + "\\output\\merged.mp4"
output_sped_up_merged_file = path + "\\output\\merged_sped_up.mp4"

print("Getting video files")
files = [f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) if f.endswith(".mp4")]

to_write = []
length = 0.00
print("Calculating expected length and formatting file locations")
files_to_delete = []
for file in files:
	abs_path = path + "\\" + file
	to_write.append(f"file '{abs_path}'\n")
	files_to_delete.append(abs_path)
	length += get_length(abs_path)

to_write[-1] = to_write[-1].replace("\n", "")
print(f"Expected length {str(length)}s")
print("Creating input file")
with open(input_file, "w") as file_to_write:
	file_to_write.writelines(to_write)

print("Calculating how fast to speed up")
if length < 3600:
	speed_up_factor = str(round(length/240))
elif length < 7200:
	speed_up_factor = str(round(length/480))
else:
	speed_up_factor = str(round(length/960))

print(f"Speeding up by {speed_up_factor}")
print("Beginning merge")
command_to_call = f'"C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe" -f concat -safe 0 -i {input_file} -codec copy -map 0:v -map 0:a -map 0:3 -copy_unknown -tag:2 gpmd {output_merged_file}'
print("Finished merging")
subprocess.call(command_to_call)
print("Deleting input file")
os.remove(input_file)
download_gpx()

for file in files_to_delete:
	os.remove(file)

output_path = path + "\\output"
if speed_up == True:
	print("Beginning to speed up and remove audio")
	command_to_call = f'"C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe" -i {output_merged_file} -filter:v "setpts=PTS/{speed_up_factor}" -an {output_sped_up_merged_file}'

	subprocess.call(command_to_call)
	print("Finished speeding up and removing audio")
	print("Cleaning up files")
	os.rename(output_path + "\\merged_sped_up.mp4", path + "\\merged_sped_up.mp4")
	os.rename(output_path + "\\merged.mp4", path + "\\merged.mp4")
	os.rename(output_path + "\\merged.gpx", path + "\\merged.gpx")
	os.rmdir(output_path)
	print("Cleaned up")
	messagebox.showinfo('Finished', f'Files merged, sped up and GPX data extracted\n\n{output_path}')
else:
	print("Cleaning up files")
	os.rename(output_path + "\\merged.mp4", path + "\\merged.mp4")
	os.rename(output_path + "\\merged.gpx", path + "\\merged.gpx")
	os.rmdir(output_path)
	print("Cleaned up")
	messagebox.showinfo('Finished', f'Files merged and GPX data extracted\n\n{output_path}')