import subprocess
import parameters
import sys
import time
import random

ns=""
divider="--------------------------------------"
se_user=False

def check_ns():
	print("Running eks deployment script")
	if sys.version_info[0] < 3:
		ns = raw_input("Enter a namespace : ")
	else:
		ns = input("Enter a namespace : ")
	print("Checking ns[{}]".format(ns))

	for x in range(parameters.NS_ATTEMPTS):
		print("Checking attempt #{}".format(x))
		p=subprocess.Popen('kubectl get ns', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		for line in p.stdout.readlines():
			spaces=line.split()
			if spaces[0].decode('ascii') == ns:
				return ""
		retval = p.wait()
		time.sleep(random.randint(1,parameters.NS_WAIT_VARIANCE))
		

	return ns

def execute_command(command):
	print(divider)
	print("Executing command : {}".format(command))
	p=subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	for line in p.stdout.readlines():
		print(line)
	retval = p.wait()

	if retval != 0:
		print ("Error encountered running command: {}".format(command))
		sys.exit(retval)

def create_namespace_yaml():
	f = open("./resources/namespace.yaml","w")
	f.write("kind: Namespace\n")
        f.write("apiVersion: v1\n")
        f.write("metadata:\n")
        f.write("  name: {0}\n".format(ns))
        f.write("  labels:\n")
        f.write("    name: {0}\n".format(ns))
	f.close()


if __name__ == "__main__":

	#Check if SE user is flagged
	if len(sys.argv) >= 2:
		if sys.argv[1] == "SEUser":
			se_user = True			

	ns = check_ns()
	if len(ns) <= 0:
		print("Namespace was already detected or cant be blank")
		sys.exit()

	create_namespace_yaml()
	execute_command("kubectl create -f ./resources/namespace.yaml")
	execute_command("kubectl create -f ./resources/serviceaccount-couchbase.yaml --namespace {}".format(ns))
	if se_user:
		execute_command("kubectl create -f ./resources/cluster-role.yaml --namespace {}".format(ns))

	execute_command("kubectl create -f ./resources/rolebinding.yaml --namespace {}".format(ns))

	# Cluster level resource only needs to be run once
	if se_user:
		execute_command("kubectl create -f ./resources/crd.yaml --namespace {}".format(ns))

	execute_command("kubectl create -f ./resources/operator.yaml --namespace {}".format(ns))
	execute_command("kubectl create -f ./resources/secret.yaml --namespace {}".format(ns))

	#Launch Couchmart Environment
	try:
		print("Found parameter")
		tag=parameters.COUCHMART_TAG
	except AttributeError:
		tag="python2"

	print("Creating couchmart from cbck/couchmart:{}".format(tag))
	execute_command("kubectl run couchmart --image=cbck/couchmart:{0} --namespace {1}".format(tag,ns))	
