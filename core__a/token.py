from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user):
    """
    Generate refresh and access tokens for a given user.

    This function generates a refresh token and an access token for the provided user.
    The access token is used for authenticating the user for subsequent requests,
    while the refresh token is used to obtain a new access token once it expires.

    Args:
        user (User): The user for whom tokens are generated.

    Returns:
        dict: A dictionary containing the refresh token and access token.

    Example:
        user = User.objects.get(username='example')
        tokens = get_tokens_for_user(user)
        # Output: {'refresh': '...', 'access': '...'}
    """
    # Generate a refresh token for the user
    refresh = RefreshToken.for_user(user)

    # Return tokens as strings for easier serialization
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
