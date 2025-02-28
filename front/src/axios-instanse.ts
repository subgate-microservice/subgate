import axios from "axios";
import {getAuthHeaders} from "./auth/auth-request.ts";
import {BACKEND_BASE_URL} from "../config.ts";

export const axiosInstance = axios.create(
    {
        baseURL: BACKEND_BASE_URL,
        headers: {
            "Accept": "application/json",
            ...getAuthHeaders(),
        },
        withCredentials: true,
    }
)