from enum import Enum


class DomException(BaseException):
    class _ErrorCode(Enum):
        NONE = 0  # Error is not recognized.
        INDEX_SIZE_ERR = 1
        DOMSTRING_SIZE_ERR = 2
        HIERARCHY_REQUEST_ERR = 3
        WRONG_DOCUMENT_ERR = 4
        INVALID_CHARACTER_ERR = 5
        NO_DATA_ALLOWED_ERR = 6
        NO_MODIFICATION_ALLOWED_ERR = 7
        NOT_FOUND_ERR = 8
        NOT_SUPPORTED_ERR = 9
        INUSE_ATTRIBUTE_ERR = 10
        INVALID_STATE_ERR = 11
        SYNTAX_ERR = 12
        INVALID_MODIFICATION_ERR = 13
        NAMESPACE_ERR = 14
        INVALID_ACCESS_ERR = 15
        VALIDATION_ERR = 16
        TYPE_MISMATCH_ERR = 17
        SECURITY_ERR = 18
        NETWORK_ERR = 19
        ABORT_ERR = 20
        URL_MISMATCH_ERR = 21
        QUOTA_EXCEEDED_ERR = 22
        TIMEOUT_ERR = 23
        INVALID_NODE_TYPE_ERR = 24
        DATA_CLONE_ERR = 25

    def __init__(self, message: str = "", name: str = "Error"):
        self.name = name
        self.message = message

    def __get_error(self) -> str:
        error_codes = {
            "IndexSizeError": "INDEX_SIZE_ERR",
            "DOMStringSizeError": "DOMSTRING_SIZE_ERR",
            "HierarchyRequestError": "HIERARCHY_REQUEST_ERR",
            "WrongDocumentError": "WRONG_DOCUMENT_ERR",
            "InvalidCharacterError": "INVALID_CHARACTER_ERR",
            "NoDataAllowedError": "NO_DATA_ALLOWED_ERR",
            "NoModificationAllowedError": "NO_MODIFICATION_ALLOWED_ERR",
            "NotFoundError": "NOT_FOUND_ERR",
            "NotSupportedError": "NOT_SUPPORTED_ERR",
            "InUseAttributeError": "INUSE_ATTRIBUTE_ERR",
            "InvalidStateError": "INVALID_STATE_ERR",
            "SyntaxError": "SYNTAX_ERR",
            "InvalidModificationError": "INVALID_MODIFICATION_ERR",
            "NamespaceError": "NAMESPACE_ERR",
            "InvalidAccessError": "INVALID_ACCESS_ERR",
            "ValidationError": "VALIDATION_ERR",
            "TypeMismatchError": "TYPE_MISMATCH_ERR",
            "SecurityError": "SECURITY_ERR",
            "NetworkError": "NETWORK_ERR",
            "AbortError": "ABORT_ERR",
            "URLMismatchError": "URL_MISMATCH_ERR",
            "QuotaExceededError": "QUOTA_EXCEEDED_ERR",
            "TimeoutError": "TIMEOUT_ERR",
            "InvalidNodeTypeError": "INVALID_NODE_TYPE_ERR",
            "DataCloneError": "DATA_CLONE_ERR",
            "EncodingError": "NONE",
            "NotReadableError": "NONE",
            "UnknownError": "NONE",
            "ConstraintError": "NONE",
            "DataError": "NONE",
            "TransactionInactiveError": "NONE",
            "ReadOnlyError": "NONE",
            "VersionError": "NONE",
            "OperationError": "NONE",
            "NotAllowedError": "NONE",
        }
        return error_codes.get(self.name, "NONE")

    def code(self) -> int:
        return self.__ErrorCode[self.__get_error()]
