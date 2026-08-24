const simpleGit = require("simple-git");
const path = require("path");
const fs = require("fs");

const cloneRepo = async (req, res) => {

    try {

        const repoUrl = req.body.repoUrl;

        const repoName = repoUrl
            .split("/")
            .pop()
            .replace(".git", "");

        const reposDir = path.join(
            __dirname,
            "../repos"
        );

        if (!fs.existsSync(reposDir)) {

            fs.mkdirSync(
                reposDir,
                { recursive: true }
            );
        }

        const repoPath = path.join(
            reposDir,
            repoName
        );

        await simpleGit().clone(
            repoUrl,
            repoPath
        );

        return res.json({

            message: "Repository cloned successfully",

            repoPath: repoPath

        });

    } catch (error) {

        console.log(error);

        return res.status(500).json({

            message: "Failed to clone repository",

            error: error.message

        });
    }
};

module.exports = {
    cloneRepo
};