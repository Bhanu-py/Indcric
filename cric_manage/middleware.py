class DebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Print GET parameters for debugging
        if request.path.startswith('/manage/manage-users/'):
            print(f"URL: {request.path}")
            print(f"GET params: {request.GET}")
            
        response = self.get_response(request)
        return response
