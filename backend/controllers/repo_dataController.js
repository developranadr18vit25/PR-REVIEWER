const mongoose = require("mongoose");
const axios = require("axios");
const { response } = require("express");

const fetchRepoData = (async (req, res) => {

    const token = req.cookies.github_access_token;

    const response = await axios.get("https://api.github.com/user/repos?affiliation=owner",
        {

            headers: {
                Authorization: `Bearer ${token}`,
                Accept: "application/vnd.github+json"
            }
        }
    )

    return res.json({
        Repos: response.data
    })
})

module.exports = {
    fetchRepoData
}