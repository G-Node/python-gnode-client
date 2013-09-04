

class GNodeSession(object)
  """
  Session class
  """
  
  def __init__(self, direcory, server=None)
    """
    Connect to local storage (and to a server)
    
    Args
      directory: dir for local data
      server: G-Node api server
    """
    pass
    
  def serch_project(fltr)
    """
    Search for projects according to connection settings (local and remote)
    
    Args
      fltr: some filter / search criteria
      
    Returns
      Array of project descriptions
    """
    pass
    
  def ls(path, fltr=None)
    """
    Display content of a certain path (local and remote)
    
    Args
      path: Path or project id
      fltr: some filter / search criteria
      
    Returns
      Array of object descriptions
    """
    pass
    
  def sync(project_id, direction="pull")
    """
    Sync a remote project with server and vice versa. If the project doesn't
    exist locally it will be downloaded completely
    
    Args
      project_id: A project id e.g. optained by search_project()
      
    Returns
      Object of the class GNodeProject
    """
    pass
    
class GNodeProject(object)
  """
  Represents a local project
  """

  def sections()
    """
    Returns all sections that are direct children of the project root
    """
    pass
    
  def blocks()
    """
    Returns all blocks that are direct children of the project root
    """
    
  def ls(path=None, fltr=None)
    """
    Display content of a certain path (the root is the project)
    
    Args
      path: Path or project id
      fltr: some filter / search criteria
      
    Returns
      Array of object descriptions
    """
    pass
    
  def search(obj_type, fltr=None)
    """
    Get all objects that match the criteria
    
    Args
      obj_type: Type of objects e.g. analogsignal
      fltr: some filter / search criteria
      
    Returns
      Array of objects
    """
    pass
