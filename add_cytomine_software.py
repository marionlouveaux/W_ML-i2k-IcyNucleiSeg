import cytomine
import sys

#Connect to cytomine, edit connection values

cytomine_host="xxx"  # Cytomine core URL
cytomine_public_key="xxx"  # Your public key
cytomine_private_key="xxx" # Your private key
id_project=

 
#Connection to Cytomine Core
conn = cytomine.Cytomine(cytomine_host, cytomine_public_key, cytomine_private_key, base_path = '/api/', working_path = '/tmp/', verbose= True)
 
execute_command = "python algo/icy_spot_detection/wrapper.py --icy_scale3sensitivity $icy_scale3sensitivity " + "--cytomine_host $host " + "--cytomine_public_key $publicKey " +"--cyto
mine_private_key $privateKey " + "--cytomine_id_project $cytomine_id_project "

#define software parameter template
software = conn.add_software("Icy_Spot_Detection", "createRabbitJobWithArgsService","ValidateAnnotation", execute_command)
conn.add_software_parameter("icy_scale3sensitivity", software.id, "Number", 40, True, 10, False)

 
#for logging (set by server)
conn.add_software_parameter("cytomine_id_software", software.id, "Number",0, True, 400, True)
conn.add_software_parameter("cytomine_id_project", software.id, "Number", 0, True, 500, True)

#add software to a given project
addSoftwareProject = conn.add_software_project(id_project,software.id)
