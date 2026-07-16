def current_project_details(project_manager, project_name: str):
    return {'name': project_name, 'exists': project_manager.exist(project_name)}
