import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyDJWWQ0dXMwpcsOzG_5uTeYh_Gcd7KVB40",
  authDomain: "disasterguardai.firebaseapp.com",
  projectId: "disasterguardai",
  storageBucket: "disasterguardai.firebasestorage.app",
  messagingSenderId: "489103464010",
  appId: "1:489103464010:web:93ef73f8929389e76778b3"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
