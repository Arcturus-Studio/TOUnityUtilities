import os
import git
import subprocess
import zipfile
import sys
import shutil
import optparse
from xml.dom import minidom

buildPlatforms = []
gitDirectory = ""
nightlyBuildDirectory = os.getcwd() + "/builds/nightlies"
windowsUnityPath = "C:\Program Files (x86)\Unity\Editor\Unity.exe"
macUnityPath = "/Applications/Unity/Unity.app/Contents/MacOS/Unity"
supportedPlatforms = ["mac", "windows", "ios"];

def unityBuildFolder():
	
	xmlPrefPath = gitDirectory + "/BuildServerPrefs.xml"
	
	if os.path.isfile(xmlPrefPath):
		xmldoc = minidom.parse(xmlPrefPath)
		itemlist = xmldoc.getElementsByTagName('build')
		return itemlist[0].attributes['folder'].value
	else:
		print "Build server preferences not found. Please create or move BuildServerPrefs.xml to " + gitDirectory + " aaa " + xmlPrefPath
		quit()

def makebuild(platform):
	
	print "Making build for " + platform
	
	unityPath = ""
	methodName = ""
	
	if os.path.isfile(macUnityPath):
		unityPath = macUnityPath
	elif os.path.isfile(windowsUnityPath):
		unityPath = windowsUnityPath
	else:
		print "Error: Unity not found"
		return
	
	if platform == 'mac':
		methodName = "BuildAutomation.MakeMacBuild"
	if platform == 'windows':
		methodName = "BuildAutomation.MakeWindowsBuild"
	if platform == 'ios':
		methodName = "BuildAutomation.MakeiOSBuild"
	
	projectDirectory = os.getcwd() + "/" + gitDirectory + unityBuildFolder()
	print projectDirectory
	
	if projectDirectory != "":
		returnCode = subprocess.call([unityPath, "-projectPath", projectDirectory, "-executeMethod", methodName, "-headless", "-quit"])
		
		if returnCode != 0:
			print "Unity build failed"
			quit()

def zipdir(dir, zip):
	#assert(isinstance(zip,ZipFile) == True)
	print "dir: " + dir
	
	if os.path.isdir(dir):
		print "its a dir"
	
	for root, dirs, files in os.walk(dir):
		for file in files:
			zip.write(os.path.join(root, file))

def findHeadForBranchName(branch, repoHeads):
	for head in repoHeads:
		if head.name == branch:
			return head

def buildNeededBranchesForRepo(repo, branches):
	for branch in branches:
		head = findHeadForBranchName(branch, repo.heads)
		if head is not None:
			currentCommit = head.commit
			repo.head.reference = head
			repo.head.reset(index=True, working_tree=True)
			newCommit = head.commit
			
			for platform in buildPlatforms:
				makebuild(platform)
				
				if platform == 'mac' or platform == 'windows':
					makezipfiles(platform, branch)
				if platform == 'ios':
					compilexcodeproject()
		else:
			print "Branch " + branch + " doesn't exist"

def makezipfiles(platform, branch):
	unityBuildDir = gitDirectory + unityBuildFolder() + "/builds"
	files = filesInDirectory(unityBuildDir)
	for file in files:
		zipfilename = (file + '.zip')
		if not os.path.isfile(zipfilename):
			zip = zipfile.ZipFile(zipfilename, 'w')
			zipdir(unityBuildDir + "/" + file, zip)
			zip.close()
			#       shutil.rmtree(file)
			
			destinationDirectory = nightlyBuildDirectory + "/" + branch
			if not os.path.isdir(nightlyBuildDirectory):
				os.makedirs(nightlyBuildDirectory)
			if not os.path.isdir(destinationDirectory):
				os.makedirs(destinationDirectory)
			shutil.move(zipfilename,destinationDirectory)

def compilexcodeproject():
	files = filesInCurrentDirectory()
	for file in files:
		if not os.path.isfile(file):
			os.chdir(os.path.join(path.abspath(sys.path[0]), file))
			retValue = subprocess.call (["xcodebuild"])
		if retValue != 0:
			print "XCode build failed."
			quit()

def filesInDirectory(dir):
	return [file for file in os.listdir(dir) if not os.path.isfile(file)]

def parseArguments(parser):
	parser.add_option("-p", "--platform", dest="platforms", help="Choose detination platform(s). Options: " + ', '.join(supportedPlatforms), metavar="PLATFORM", action="append")
	parser.add_option("-r", "--repo", dest="repo", help="Directory repo to build", metavar="DIRECTORY")
	parser.add_option("-b", "--branches", dest="branches", help="One or more branches to checkout and make builds from", action="append")
	
	return parser.parse_args()

def validatePlatformArguments(platforms):
	for platform in platforms:
		if platform not in supportedPlatforms:
			parser.error("Platform is not supported. Try ios, mac, or windows")
			quit()

if __name__ == '__main__':
	
	parser = optparse.OptionParser()
	(options, args) = parseArguments(parser)
	
	gitDirectory = options.repo
	buildPlatforms = options.platforms
	validatePlatformArguments(buildPlatforms)
	
	if os.path.exists(gitDirectory):
		repo = git.Repo(gitDirectory)
		buildNeededBranchesForRepo(repo, options.branches)
	else:
		print "Error: Git repo does not exist: %s" % gitDirectory
