const express=require("express");
const router=express.Router()
const repo_dataController=require("../controllers/repo_dataController")
const repo_cloneController=require("../controllers/repoCloneController")


router.route("/repos")
    .get(repo_dataController.fetchRepoData)

router.route("/cloneRepo")
    .post(repo_cloneController.cloneRepo)

module.exports=router;