import axios from "axios";
import {BACKEND_BASE_URL} from "../config.ts";

export const axiosInstance = axios.create(
    {
        baseURL: BACKEND_BASE_URL,
        headers: {
            "Accept": "application/json",
        },
        withCredentials: true,
    }
)