import cytomine
import sys

def add_software(cytomine_host, cytomine_public_key, cytomine_private_key, id_project=None):
    #Connection to Cytomine Core
    conn = cytomine.Cytomine(cytomine_host, cytomine_public_key, cytomine_private_key, base_path = '/api/', working_path = '/tmp/', verbose= True)

    execute_command = "python algo/W_SpotDetection-Icy/wrapper.py --icy_scale3sensitivity $icy_scale3sensitivity " \
                      + "--cytomine_host $host " \
                      + "--cytomine_public_key $publicKey " \
                      + "--cytomine_private_key $privateKey " \
                      + "--cytomine_id_project $cytomine_id_project "

    #define software parameter template
    software = conn.add_software("W_SpotDetection-Icy", "createRabbitJobWithArgsService","ValidateAnnotation", execute_command)
    conn.add_software_parameter("icy_scale3sensitivity", software.id, "Number", 40, True, 10, False)


    #for logging (set by server)
    conn.add_software_parameter("cytomine_id_software", software.id, "Number",0, True, 400, True)
    conn.add_software_parameter("cytomine_id_project", software.id, "Number", 0, True, 500, True)

    if id_project:
        #add software to a given project
        addSoftwareProject = conn.add_software_project(id_project,software.id)


if __name__ == '__main__':
    """
    Arguments:
    1) Cytomine host
    2) Cytomine public key
    3) Cytomine private key
    4) (Optional) Cytomine project ID to link with new software
    """
    add_software(*sys.argv[1:])
